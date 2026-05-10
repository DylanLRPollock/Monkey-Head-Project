<# 
Monkey Head Project / HueyOS
Windows Installer (PowerShell)

This script is intended to replace the older multi-file batch setup flow
(00-WIN11.bat, 01-FULL.bat, 02-MINI.bat, etc.) with a single, robust installer.

Primary logic sourced from:
- 01-FULL.bat: Chocolatey install, tool install, git clone w/ submodules, venv, pip install, memory dirs, license GUI
- 02-MINI.bat: minimal setup option (reduced tool installation)

Notes:
- Default install location is system-wide (Program Files) and will auto-elevate.
- Use -UserInstall for per-user install (no admin required if you also skip tool installs).
#>

[CmdletBinding()]
param(
  # Where Monkey-Head-Project will be installed
  [string]$InstallDir,

  # Where shared "memory" lives (defaults to "$InstallDir\memory")
  [string]$MemoryPath,

  # Git repo to install from
  [string]$RepoUrl = "https://github.com/DylanLRPollock/Monkey-Head-Project.git",

  # Optional branch name. If omitted, uses repo default branch.
  [string]$Branch = "",

  # Install to a per-user location (LOCALAPPDATA) instead of Program Files.
  [switch]$UserInstall,

  # Install a "full" dev environment (Node.js, VS Code, Docker Desktop).
  [switch]$Full,

  # Install additional optional tools (Postman, Slack, etc.).
  [switch]$InstallOptionalTools,

  # Skip Chocolatey bootstrap (assumes choco is already available).
  [switch]$SkipChocolatey,

  # Skip installing tools (git/python/etc.). Useful if you manage deps yourself.
  [switch]$SkipToolInstall,

  # If the install directory already exists, overwrite it (preserving memory by default).
  [switch]$Force,

  # Do not show interactive prompts / GUI (license GUI will be skipped).
  [switch]$NonInteractive,

  # If provided, indicates the user accepts the license (used to skip license GUI).
  [switch]$AcceptLicense
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# -----------------------------
# Logging
# -----------------------------
$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogPath = Join-Path $env:TEMP "HueyOS_install_$Timestamp.log"

function Write-Log {
  param(
    [Parameter(Mandatory=$true)][string]$Message,
    [ValidateSet('INFO','WARN','ERROR','DEBUG')][string]$Level = 'INFO'
  )
  $line = "{0} [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Message
  Write-Host $line
  try { Add-Content -Path $LogPath -Value $line -Encoding UTF8 } catch { }
}

function Fail {
  param([string]$Message, [int]$Code = 1)
  Write-Log $Message 'ERROR'
  Write-Log "Log: $LogPath" 'ERROR'
  exit $Code
}

# -----------------------------
# Helpers
# -----------------------------
function Test-IsAdmin {
  try {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p  = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch {
    return $false
  }
}

function Ensure-ElevationIfNeeded {
  param([bool]$NeedsElevation)

  if (-not $NeedsElevation) { return }

  if (Test-IsAdmin) { return }

  Write-Log "Elevation required. Relaunching as Administrator..." 'INFO'
  $argList = @("-NoProfile","-ExecutionPolicy","Bypass","-File", $PSCommandPath) + $args
  try {
    Start-Process -FilePath "powershell.exe" -Verb RunAs -WorkingDirectory (Get-Location).Path -ArgumentList $argList | Out-Null
    exit 0
  } catch {
    Fail "Unable to elevate. Re-run this script from an Administrator PowerShell session."
  }
}

function Refresh-PathFromRegistry {
  # Ensures newly installed executables are usable in this session
  $machine = [Environment]::GetEnvironmentVariable('Path','Machine')
  $user    = [Environment]::GetEnvironmentVariable('Path','User')
  if ([string]::IsNullOrWhiteSpace($machine)) { $machine = "" }
  if ([string]::IsNullOrWhiteSpace($user)) { $user = "" }
  $env:Path = "$machine;$user"
}

function Test-Internet {
  try {
    $null = Invoke-WebRequest -UseBasicParsing -Uri "https://github.com" -Method Head -TimeoutSec 15
    return $true
  } catch {
    return $false
  }
}

function Invoke-Native {
  param(
    [Parameter(Mandatory=$true)][string]$Exe,
    [string[]]$Args = @(),
    [string]$WorkingDirectory = (Get-Location).Path,
    [switch]$AllowNonZero
  )
  Push-Location $WorkingDirectory
  try {
    Write-Log ("Running: {0} {1}" -f $Exe, ($Args -join ' ')) 'DEBUG'
    & $Exe @Args
    $code = $LASTEXITCODE
    if (-not $AllowNonZero -and $code -ne 0) {
      throw "ExitCode=$code"
    }
    return $code
  } finally {
    Pop-Location
  }
}

function Ensure-Chocolatey {
  if ($SkipChocolatey) {
    Write-Log "Skipping Chocolatey bootstrap (-SkipChocolatey)." 'INFO'
    return
  }

  if (Get-Command choco -ErrorAction SilentlyContinue) {
    Write-Log "Chocolatey already present." 'INFO'
    return
  }

  Write-Log "Installing Chocolatey..." 'INFO'
  try {
    Set-ExecutionPolicy Bypass -Scope Process -Force | Out-Null
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
  } catch {
    Fail "Chocolatey installation failed. Error: $($_.Exception.Message)"
  }

  Refresh-PathFromRegistry

  if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Fail "Chocolatey install completed but 'choco' is still not available in PATH."
  }
  Write-Log "Chocolatey installed successfully." 'INFO'
}

function Test-ChocoInstalled {
  param([Parameter(Mandatory=$true)][string]$Package)
  if (-not (Get-Command choco -ErrorAction SilentlyContinue)) { return $false }
  $out = & choco list --local-only --exact $Package --limit-output 2>$null
  if ($LASTEXITCODE -ne 0) { return $false }
  return ($out -match "^$([regex]::Escape($Package))\|")
}

function Ensure-ChocoPackage {
  param(
    [Parameter(Mandatory=$true)][string]$Package,
    [string[]]$ExtraArgs = @()
  )
  if (Test-ChocoInstalled $Package) {
    Write-Log "Chocolatey package already installed: $Package" 'INFO'
    return $false
  }

  Write-Log "Installing Chocolatey package: $Package" 'INFO'
  Invoke-Native -Exe "choco" -Args (@("install","-y",$Package,"--no-progress") + $ExtraArgs)
  Refresh-PathFromRegistry
  return $true
}

function Get-PythonInvocation {
  # Prefer the Python launcher if present (py -3), otherwise python.exe
  if (Get-Command py -ErrorAction SilentlyContinue) {
    return ,@("py","-3")
  }
  if (Get-Command python -ErrorAction SilentlyContinue) {
    return ,@("python")
  }
  if (Get-Command python3 -ErrorAction SilentlyContinue) {
    return ,@("python3")
  }
  return $null
}

function Get-PythonVersionTuple {
  param([string]$PyExe, [string[]]$PyBaseArgs)

  $code = "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
  $ver = & $PyExe @PyBaseArgs -c $code 2>$null
  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($ver)) { return $null }
  return $ver.Trim()
}

function Ensure-PythonMinVersion {
  param([int]$MinMajor = 3, [int]$MinMinor = 10)

  $py = Get-PythonInvocation
  if (-not $py) { return $false }

  $pyExe = $py[0]
  $pyBaseArgs = @()
  if ($py.Count -gt 1) { $pyBaseArgs = $py[1..($py.Count-1)] }

  $v = Get-PythonVersionTuple -PyExe $pyExe -PyBaseArgs $pyBaseArgs
  if (-not $v) { return $false }

  $parts = $v.Split('.')
  if ($parts.Count -lt 2) { return $false }
  $maj = [int]$parts[0]
  $min = [int]$parts[1]

  if ($maj -lt $MinMajor) { return $false }
  if ($maj -eq $MinMajor -and $min -lt $MinMinor) { return $false }
  return $true
}

function Ensure-Directory {
  param([Parameter(Mandatory=$true)][string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
  }
}

function Is-PathUnder {
  param(
    [Parameter(Mandatory=$true)][string]$Child,
    [Parameter(Mandatory=$true)][string]$Parent
  )
  try {
    $c = [IO.Path]::GetFullPath($Child.TrimEnd('\') + '\')
    $p = [IO.Path]::GetFullPath($Parent.TrimEnd('\') + '\')
    return $c.StartsWith($p, [System.StringComparison]::OrdinalIgnoreCase)
  } catch {
    return $false
  }
}

# -----------------------------
# Defaults
# -----------------------------
if ([string]::IsNullOrWhiteSpace($InstallDir)) {
  if ($UserInstall) {
    $InstallDir = Join-Path $env:LOCALAPPDATA "Programs\Monkey-Head-Project"
  } else {
    $InstallDir = Join-Path $env:ProgramFiles "Monkey-Head-Project"
  }
}
if ([string]::IsNullOrWhiteSpace($MemoryPath)) {
  $MemoryPath = Join-Path $InstallDir "memory"
}

# Determine if we need admin:
# - Installing into Program Files, OR
# - Installing tools via Chocolatey (default), which requires elevation
$needsAdminForPath = Is-PathUnder -Child $InstallDir -Parent $env:ProgramFiles
$needsAdminForTools = (-not $SkipToolInstall)
# Tool installation via Chocolatey typically requires elevation even for per-user installs.
$needsElevation = ($needsAdminForPath -or $needsAdminForTools)

Ensure-ElevationIfNeeded -NeedsElevation:$needsElevation

Write-Log "InstallDir : $InstallDir" 'INFO'
Write-Log "MemoryPath : $MemoryPath" 'INFO'
Write-Log "RepoUrl    : $RepoUrl" 'INFO'
if ($Branch) { Write-Log "Branch     : $Branch" 'INFO' }
Write-Log "Full       : $([bool]$Full)" 'INFO'
Write-Log "Optional   : $([bool]$InstallOptionalTools)" 'INFO'
Write-Log "Log        : $LogPath" 'INFO'

# -----------------------------
# System checks (from 01-FULL.bat / 00-WIN11.bat)
# -----------------------------
try {
  $os = [System.Environment]::OSVersion.Version
  Write-Log "OS Version: $os" 'INFO'
} catch { }

$driveName = ($env:SystemDrive -replace ':','')
try {
  $drive = Get-PSDrive -Name $driveName -ErrorAction Stop
  $freeGB = [math]::Round(($drive.Free/1GB),2)
  Write-Log "Free space on $($env:SystemDrive): $freeGB GB" 'INFO'
} catch {
  Write-Log "Unable to read free disk space." 'WARN'
}

if (-not (Test-Internet)) {
  Fail "No internet connectivity detected (unable to reach https://github.com)."
}

# -----------------------------
# Tooling (Chocolatey + packages)
# -----------------------------
$installedChocoPkgs = New-Object System.Collections.Generic.List[string]

if (-not $SkipToolInstall) {
  Ensure-Chocolatey

  $required = @("git","python")
  if ($Full) {
    $required += @("nodejs","vscode","docker-desktop")
  }

  foreach ($pkg in $required) {
    $didInstall = Ensure-ChocoPackage -Package $pkg
    if ($didInstall) { $installedChocoPkgs.Add($pkg) }
  }

  if ($InstallOptionalTools) {
    # Directly derived from 01-FULL.bat optional list.
    $optional = @(
      "postman",
      "slack",
      "zoom",
      "7zip",
      "wget",
      "curl",
      "terraform",
      "kubernetes-cli",
      "minikube",
      "awscli",
      "azure-cli"
    )
    foreach ($pkg in $optional) {
      $didInstall = Ensure-ChocoPackage -Package $pkg
      if ($didInstall) { $installedChocoPkgs.Add($pkg) }
    }
  }
} else {
  Write-Log "Skipping tool installation (-SkipToolInstall)." 'INFO'
}

# Validate python
if (-not (Ensure-PythonMinVersion -MinMajor 3 -MinMinor 10)) {
  Fail "Python 3.10+ not detected in PATH. Install it (e.g., via Chocolatey) or re-run without -SkipToolInstall."
}

$py = Get-PythonInvocation
$pyExe = $py[0]
$pyBaseArgs = @()
if ($py.Count -gt 1) { $pyBaseArgs = $py[1..($py.Count-1)] }

# Validate git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Fail "git not found in PATH. Install git or re-run without -SkipToolInstall."
}

# -----------------------------
# Prepare install directory
# -----------------------------
$memoryWasPreserved = $false
$tempMemoryBackup = $null

if (Test-Path -LiteralPath $InstallDir) {
  $hasAnyFiles = @(Get-ChildItem -LiteralPath $InstallDir -Force -ErrorAction SilentlyContinue).Count -gt 0
  if ($hasAnyFiles) {
    if (-not $Force) {
      Fail "InstallDir already exists and is not empty. Re-run with -Force to overwrite: $InstallDir"
    }

    # Preserve memory if it lives under InstallDir and exists
    if (Is-PathUnder -Child $MemoryPath -Parent $InstallDir -and (Test-Path -LiteralPath $MemoryPath)) {
      $tempMemoryBackup = Join-Path $env:TEMP ("HueyOS_memory_backup_{0}" -f $Timestamp)
      Write-Log "Preserving memory: moving '$MemoryPath' -> '$tempMemoryBackup'" 'INFO'
      try {
        Move-Item -LiteralPath $MemoryPath -Destination $tempMemoryBackup -Force
        $memoryWasPreserved = $true
      } catch {
        Fail "Failed to preserve memory directory. Error: $($_.Exception.Message)"
      }
    }

    Write-Log "Removing existing install directory contents: $InstallDir" 'WARN'
    try {
      Remove-Item -LiteralPath $InstallDir -Recurse -Force
    } catch {
      Fail "Failed to remove existing install directory. Error: $($_.Exception.Message)"
    }
  }
}

Ensure-Directory -Path $InstallDir

# -----------------------------
# Clone repo (from 01-FULL.bat)
# -----------------------------
Write-Log "Cloning repository..." 'INFO'
try {
  $cloneArgs = @("clone","--recurse-submodules")
  if (-not [string]::IsNullOrWhiteSpace($Branch)) {
    $cloneArgs += @("--branch",$Branch,"--single-branch")
  }
  $cloneArgs += @($RepoUrl,".")
  Invoke-Native -Exe "git" -Args $cloneArgs -WorkingDirectory $InstallDir

  Invoke-Native -Exe "git" -Args @("submodule","sync","--recursive") -WorkingDirectory $InstallDir -AllowNonZero
  Invoke-Native -Exe "git" -Args @("submodule","update","--init","--recursive") -WorkingDirectory $InstallDir
} catch {
  Fail "Git clone failed. Error: $($_.Exception.Message)"
}

# Restore preserved memory if we moved it
if ($memoryWasPreserved -and $tempMemoryBackup -and (Test-Path -LiteralPath $tempMemoryBackup)) {
  try {
    Ensure-Directory -Path (Split-Path -Parent $MemoryPath)
    Write-Log "Restoring preserved memory: '$tempMemoryBackup' -> '$MemoryPath'" 'INFO'
    Move-Item -LiteralPath $tempMemoryBackup -Destination $MemoryPath -Force
  } catch {
    Fail "Failed to restore preserved memory directory. Error: $($_.Exception.Message)"
  }
}

# -----------------------------
# Prepare memory directories (from 01-FULL.bat)
# -----------------------------
Write-Log "Preparing memory directories..." 'INFO'
try {
  Ensure-Directory -Path $MemoryPath
  Ensure-Directory -Path (Join-Path $MemoryPath "LOGS")
  Ensure-Directory -Path (Join-Path $MemoryPath "RAW")
} catch {
  Fail "Failed to create memory directories at '$MemoryPath'. Error: $($_.Exception.Message)"
}

# -----------------------------
# Python virtualenv + requirements (from 01-FULL.bat)
# -----------------------------
$venvDir = Join-Path $InstallDir "venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$venvPip = Join-Path $venvDir "Scripts\pip.exe"

Write-Log "Setting up Python virtual environment..." 'INFO'
try {
  if (Test-Path -LiteralPath $venvDir) {
    Write-Log "Existing venv detected. Removing (install is authoritative)..." 'WARN'
    Remove-Item -LiteralPath $venvDir -Recurse -Force
  }

  Invoke-Native -Exe $pyExe -Args ($pyBaseArgs + @("-m","venv",$venvDir)) -WorkingDirectory $InstallDir

  if (-not (Test-Path -LiteralPath $venvPython)) {
    Fail "venv created but python.exe not found at: $venvPython"
  }

  Invoke-Native -Exe $venvPython -Args @("-m","pip","install","--upgrade","pip") -WorkingDirectory $InstallDir

  $req = Join-Path $InstallDir "requirements.txt"
  if (Test-Path -LiteralPath $req) {
    Invoke-Native -Exe $venvPip -Args @("install","-r",$req) -WorkingDirectory $InstallDir
  } else {
    Write-Log "requirements.txt not found; skipping pip install -r." 'WARN'
  }

  # Install vendored pygpt-MHP package (if present)
  $pygptPath = Join-Path $InstallDir "vendor\pygpt\pygpt-mhp"
  if (Test-Path -LiteralPath $pygptPath) {
    Invoke-Native -Exe $venvPip -Args @("install","-e",$pygptPath) -WorkingDirectory $InstallDir
  } else {
    Write-Log "Vendor path not found (vendor\pygpt\pygpt-mhp). Skipping editable install." 'WARN'
  }

  # Sync structure + connectivity checks (if present)
  $syncScript = Join-Path $InstallDir "sync_pygpt_structure.py"
  if (Test-Path -LiteralPath $syncScript) {
    Invoke-Native -Exe $venvPython -Args @($syncScript) -WorkingDirectory $InstallDir
  } else {
    Write-Log "sync_pygpt_structure.py not found; skipping." 'WARN'
  }

  $connScript = Join-Path $InstallDir "scripts\check_inter_program_connectivity.py"
  if (Test-Path -LiteralPath $connScript) {
    Invoke-Native -Exe $venvPython -Args @($connScript) -WorkingDirectory $InstallDir
  } else {
    Write-Log "scripts\check_inter_program_connectivity.py not found; skipping." 'WARN'
  }

} catch {
  Fail "Python environment setup failed. Error: $($_.Exception.Message)"
}

# -----------------------------
# License GUI (from 01-FULL.bat) - optional
# -----------------------------
if ($NonInteractive -or $AcceptLicense) {
  Write-Log "Skipping license GUI (NonInteractive/AcceptLicense)." 'INFO'
} else {
  $licenseGui = Join-Path $InstallDir "src\license_gui.py"
  if (Test-Path -LiteralPath $licenseGui) {
    Write-Log "Displaying license agreement GUI..." 'INFO'
    try {
      Invoke-Native -Exe $venvPython -Args @($licenseGui) -WorkingDirectory $InstallDir -AllowNonZero
    } catch {
      Write-Log "License GUI failed or was closed. Continuing. Error: $($_.Exception.Message)" 'WARN'
    }
  } else {
    Write-Log "License GUI not found at src\license_gui.py; skipping." 'WARN'
  }
}

# -----------------------------
# Install metadata (for update/uninstall scripts)
# -----------------------------
try {
  $meta = [ordered]@{
    schemaVersion = 1
    installedAt   = (Get-Date).ToString("o")
    installDir    = $InstallDir
    memoryPath    = $MemoryPath
    repoUrl       = $RepoUrl
    branch        = $Branch
    full          = [bool]$Full
    optionalTools = [bool]$InstallOptionalTools
    chocoPackagesInstalled = @($installedChocoPkgs)
    logPath       = $LogPath
  }

  $metaPath = Join-Path $InstallDir "hueyos_install.json"
  $meta | ConvertTo-Json -Depth 6 | Out-File -FilePath $metaPath -Encoding UTF8

  $depsPath = Join-Path $InstallDir "hueyos_choco_deps.json"
  @($installedChocoPkgs) | ConvertTo-Json -Depth 3 | Out-File -FilePath $depsPath -Encoding UTF8

  Write-Log "Wrote install metadata: $metaPath" 'INFO'
} catch {
  Write-Log "Failed to write install metadata. Error: $($_.Exception.Message)" 'WARN'
}

Write-Log "Installation complete." 'INFO'
Write-Host ""
Write-Host "***********************************************"
Write-Host "  Monkey Head Project / HueyOS installed."
Write-Host "  InstallDir: $InstallDir"
Write-Host "  Memory:     $MemoryPath"
Write-Host "  Log:        $LogPath"
Write-Host "***********************************************"
