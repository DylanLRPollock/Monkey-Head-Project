<#
Monkey Head Project / HueyOS
Windows Updater (PowerShell)

Primary logic sourced from:
- 01-FULL.bat: venv/pip flow, submodules, sync scripts
- 05-UPDATE.bat: optional "toolchain updates" (Chocolatey/NPM/PIP/VSCode extensions/Docker images)

This update script focuses on updating the installed project safely:
- Updates git checkout (fast-forward by default)
- Updates submodules
- Updates Python venv dependencies
- Preserves memory directory by default

If you want global tool updates similar to 05-UPDATE.bat, pass -UpdateTools.
#>

[CmdletBinding()]
param(
  # Install directory of Monkey-Head-Project. If omitted, script will attempt to locate it.
  [string]$InstallDir,

  # Optional branch name to update to (for git installs)
  [string]$Branch = "",

  # Recreate the virtual environment from scratch.
  [switch]$RecreateVenv,

  # If repo has local modifications, do NOT stop; discard changes and reset to origin/<branch>.
  [switch]$Force,

  # Stash local changes before updating (git only). Mutually exclusive with -Force.
  [switch]$Stash,

  # Update global tools similar to 05-UPDATE.bat (Chocolatey upgrades, npm -g, etc.). Requires admin.
  [switch]$UpdateTools,

  # Skip Python dependency updates (git update only).
  [switch]$SkipPython,

  # Do not show interactive prompts / GUI.
  [switch]$NonInteractive
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogPath = Join-Path $env:TEMP "HueyOS_update_$Timestamp.log"

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

function Test-IsAdmin {
  try {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p  = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch { return $false }
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
  $machine = [Environment]::GetEnvironmentVariable('Path','Machine')
  $user    = [Environment]::GetEnvironmentVariable('Path','User')
  if ([string]::IsNullOrWhiteSpace($machine)) { $machine = "" }
  if ([string]::IsNullOrWhiteSpace($user)) { $user = "" }
  $env:Path = "$machine;$user"
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

function Load-Metadata {
  param([string]$Dir)
  $metaPath = Join-Path $Dir "hueyos_install.json"
  if (-not (Test-Path -LiteralPath $metaPath)) { return $null }
  try {
    return (Get-Content -LiteralPath $metaPath -Raw -Encoding UTF8 | ConvertFrom-Json)
  } catch {
    Write-Log "Failed to parse metadata at $metaPath. Error: $($_.Exception.Message)" 'WARN'
    return $null
  }
}

function Find-InstallDir {
  param([string]$Explicit)

  if (-not [string]::IsNullOrWhiteSpace($Explicit)) { return $Explicit }

  $candidates = @(
    (Join-Path $env:ProgramFiles "Monkey-Head-Project"),
    (Join-Path $env:LOCALAPPDATA "Programs\Monkey-Head-Project")
  )
  foreach ($c in $candidates) {
    $meta = Load-Metadata -Dir $c
    if ($meta -and (Test-Path -LiteralPath $c)) {
      return $c
    }
  }
  # Fallback to existing directory even without metadata
  foreach ($c in $candidates) {
    if (Test-Path -LiteralPath $c) { return $c }
  }
  return $null
}

function Ensure-ChocolateyPresent {
  if (Get-Command choco -ErrorAction SilentlyContinue) { return $true }
  return $false
}

function Update-Tools {
  # Derived from 05-UPDATE.bat, but behind an explicit flag.
  if (-not (Ensure-ChocolateyPresent)) {
    Write-Log "Chocolatey not found; skipping choco updates." 'WARN'
  } else {
    Write-Log "Updating Chocolatey + packages (choco upgrade)..." 'INFO'
    Invoke-Native -Exe "choco" -Args @("upgrade","chocolatey","-y","--no-progress") -AllowNonZero
    Invoke-Native -Exe "choco" -Args @("upgrade","all","-y","--no-progress") -AllowNonZero
  }

  if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Log "Updating npm global packages..." 'INFO'
    Invoke-Native -Exe "npm" -Args @("update","-g") -AllowNonZero
  } else {
    Write-Log "npm not found; skipping npm -g updates." 'WARN'
  }

  if (Get-Command code -ErrorAction SilentlyContinue) {
    Write-Log "Updating VS Code extensions..." 'INFO'
    try {
      $exts = & code --list-extensions 2>$null
      foreach ($e in $exts) {
        if ([string]::IsNullOrWhiteSpace($e)) { continue }
        & code --install-extension $e 2>$null | Out-Null
      }
    } catch {
      Write-Log "VS Code extension update failed. Error: $($_.Exception.Message)" 'WARN'
    }
  } else {
    Write-Log "VS Code CLI (code) not found; skipping extension updates." 'WARN'
  }

  if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Log "Pulling Docker images currently present (best-effort)..." 'INFO'
    try {
      $imgs = & docker images --format "{{.Repository}}:{{.Tag}}" 2>$null | Where-Object { $_ -and ($_ -notmatch "<none>") }
      foreach ($img in $imgs) {
        & docker pull $img 2>$null | Out-Null
      }
    } catch {
      Write-Log "Docker image update failed. Error: $($_.Exception.Message)" 'WARN'
    }
  } else {
    Write-Log "docker not found; skipping docker image pulls." 'WARN'
  }

  # PowerShell module updates can be noisy and sometimes require PSGallery trust prompts.
  # Only attempt in interactive sessions.
  if (-not $NonInteractive) {
    try {
      Write-Log "Updating PowerShell modules (best-effort)..." 'INFO'
      powershell -NoProfile -Command "Get-InstalledModule -ErrorAction SilentlyContinue | ForEach-Object { try { Update-Module -Name $_.Name -Force -ErrorAction Stop } catch {} }" | Out-Null
    } catch {
      Write-Log "PowerShell module update step failed. Error: $($_.Exception.Message)" 'WARN'
    }
  }
}

# -----------------------------
# Resolve install dir + metadata
# -----------------------------
$InstallDir = Find-InstallDir -Explicit $InstallDir
if (-not $InstallDir) { Fail "Could not locate an installation. Provide -InstallDir explicitly." }

if (-not (Test-Path -LiteralPath $InstallDir)) { Fail "InstallDir not found: $InstallDir" }

$meta = Load-Metadata -Dir $InstallDir
$repoUrl = $null
$memoryPath = $null
if ($meta) {
  $repoUrl = $meta.repoUrl
  $memoryPath = $meta.memoryPath
  if ([string]::IsNullOrWhiteSpace($Branch) -and $meta.branch) { $Branch = $meta.branch }
}

Write-Log "InstallDir: $InstallDir" 'INFO'
if ($memoryPath) { Write-Log "MemoryPath: $memoryPath" 'INFO' }
Write-Log "Log: $LogPath" 'INFO'

# Admin requirement:
# - Updating global tools requires admin
# - Updating a Program Files install typically requires admin
$needsAdmin = $false
try {
  $pf = [IO.Path]::GetFullPath($env:ProgramFiles.TrimEnd('\') + '\')
  $id = [IO.Path]::GetFullPath($InstallDir.TrimEnd('\') + '\')
  if ($id.StartsWith($pf, [System.StringComparison]::OrdinalIgnoreCase)) { $needsAdmin = $true }
} catch { }

if ($UpdateTools) { $needsAdmin = $true }
Ensure-ElevationIfNeeded -NeedsElevation:$needsAdmin

Refresh-PathFromRegistry

# -----------------------------
# Update tools (optional)
# -----------------------------
if ($UpdateTools) {
  Update-Tools
}

# -----------------------------
# Update git checkout (if present)
# -----------------------------
$gitDir = Join-Path $InstallDir ".git"
if (Test-Path -LiteralPath $gitDir) {
  if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Fail "git not found in PATH; cannot update repository."
  }

  if ($Stash -and $Force) {
    Fail "Use only one of -Stash or -Force."
  }

  Write-Log "Updating git repository..." 'INFO'

  # Detect local changes
  $status = & git -C $InstallDir status --porcelain 2>$null
  if ($LASTEXITCODE -ne 0) { Fail "git status failed." }

  $isDirty = -not [string]::IsNullOrWhiteSpace(($status | Out-String).Trim())
  if ($isDirty) {
    if ($Force) {
      Write-Log "Working tree is dirty; -Force specified, discarding local changes." 'WARN'
    } elseif ($Stash) {
      Write-Log "Working tree is dirty; stashing local changes." 'WARN'
      Invoke-Native -Exe "git" -Args @("-C",$InstallDir,"stash","push","-u","-m","HueyOS update stash $Timestamp") -AllowNonZero
    } else {
      Fail "Working tree has local changes. Re-run with -Stash or -Force."
    }
  }

  Invoke-Native -Exe "git" -Args @("-C",$InstallDir,"fetch","--all","--prune")

  # Determine branch if not supplied
  if ([string]::IsNullOrWhiteSpace($Branch)) {
    $Branch = (& git -C $InstallDir rev-parse --abbrev-ref HEAD 2>$null).Trim()
  }
  if ([string]::IsNullOrWhiteSpace($Branch)) {
    $Branch = "main"
  }
  Write-Log "Branch: $Branch" 'INFO'

  # Attempt ff-only pull
  $pullOk = $true
  try {
    Invoke-Native -Exe "git" -Args @("-C",$InstallDir,"pull","--ff-only","origin",$Branch) -AllowNonZero
    if ($LASTEXITCODE -ne 0) { $pullOk = $false }
  } catch { $pullOk = $false }

  if (-not $pullOk) {
    if ($Force) {
      Write-Log "Fast-forward pull failed; forcing reset to origin/$Branch" 'WARN'
      Invoke-Native -Exe "git" -Args @("-C",$InstallDir,"reset","--hard","origin/$Branch")
      Invoke-Native -Exe "git" -Args @("-C",$InstallDir,"clean","-fd")
    } else {
      Fail "git pull --ff-only failed (non fast-forward). Re-run with -Force to reset."
    }
  }

  # Submodules (from 01-FULL.bat)
  Invoke-Native -Exe "git" -Args @("-C",$InstallDir,"submodule","sync","--recursive") -AllowNonZero
  Invoke-Native -Exe "git" -Args @("-C",$InstallDir,"submodule","update","--init","--recursive")
} else {
  # Non-git install: best-effort rehydrate from repoUrl
  if ([string]::IsNullOrWhiteSpace($repoUrl)) {
    $repoUrl = "https://github.com/DylanLRPollock/Monkey-Head-Project.git"
  }
  if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Fail "Install is not a git checkout and git is not available; cannot update."
  }

  Write-Log "InstallDir is not a git checkout; performing best-effort refresh via temp clone." 'WARN'
  $tmp = Join-Path $env:TEMP ("HueyOS_update_clone_{0}" -f $Timestamp)
  New-Item -ItemType Directory -Path $tmp -Force | Out-Null
  try {
    Invoke-Native -Exe "git" -Args @("clone","--recurse-submodules",$repoUrl,$tmp)
    # Copy over (does not delete old files; safe default)
    Write-Log "Copying updated files into InstallDir (safe, non-destructive)..." 'INFO'
    Copy-Item -Path (Join-Path $tmp "*") -Destination $InstallDir -Recurse -Force
  } finally {
    try { Remove-Item -LiteralPath $tmp -Recurse -Force } catch { }
  }
}

# -----------------------------
# Python venv update (from 01-FULL.bat)
# -----------------------------
if (-not $SkipPython) {
  $venvDir = Join-Path $InstallDir "venv"
  $venvPython = Join-Path $venvDir "Scripts\python.exe"
  $venvPip = Join-Path $venvDir "Scripts\pip.exe"

  # Determine base python to create venv if needed
  function Get-PythonInvocation {
    if (Get-Command py -ErrorAction SilentlyContinue) { return ,@("py","-3") }
    if (Get-Command python -ErrorAction SilentlyContinue) { return ,@("python") }
    if (Get-Command python3 -ErrorAction SilentlyContinue) { return ,@("python3") }
    return $null
  }

  $py = Get-PythonInvocation
  if (-not $py) { Fail "Python not found in PATH; cannot update Python environment." }
  $pyExe = $py[0]
  $pyBaseArgs = @()
  if ($py.Count -gt 1) { $pyBaseArgs = $py[1..($py.Count-1)] }

  if ($RecreateVenv -and (Test-Path -LiteralPath $venvDir)) {
    Write-Log "Recreating venv: removing $venvDir" 'WARN'
    Remove-Item -LiteralPath $venvDir -Recurse -Force
  }

  if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Log "venv not found; creating new venv..." 'INFO'
    Invoke-Native -Exe $pyExe -Args ($pyBaseArgs + @("-m","venv",$venvDir)) -WorkingDirectory $InstallDir
  }

  if (-not (Test-Path -LiteralPath $venvPython)) {
    Fail "venv python not found at: $venvPython"
  }

  Write-Log "Upgrading pip + installing requirements..." 'INFO'
  Invoke-Native -Exe $venvPython -Args @("-m","pip","install","--upgrade","pip") -WorkingDirectory $InstallDir -AllowNonZero

  $req = Join-Path $InstallDir "requirements.txt"
  if (Test-Path -LiteralPath $req) {
    Invoke-Native -Exe $venvPip -Args @("install","-r",$req) -WorkingDirectory $InstallDir -AllowNonZero
  } else {
    Write-Log "requirements.txt not found; skipping pip -r." 'WARN'
  }

  $pygptPath = Join-Path $InstallDir "vendor\pygpt\pygpt-mhp"
  if (Test-Path -LiteralPath $pygptPath) {
    Invoke-Native -Exe $venvPip -Args @("install","-e",$pygptPath) -WorkingDirectory $InstallDir -AllowNonZero
  }

  $syncScript = Join-Path $InstallDir "sync_pygpt_structure.py"
  if (Test-Path -LiteralPath $syncScript) {
    Invoke-Native -Exe $venvPython -Args @($syncScript) -WorkingDirectory $InstallDir -AllowNonZero
  }

  $connScript = Join-Path $InstallDir "scripts\check_inter_program_connectivity.py"
  if (Test-Path -LiteralPath $connScript) {
    Invoke-Native -Exe $venvPython -Args @($connScript) -WorkingDirectory $InstallDir -AllowNonZero
  }
} else {
  Write-Log "Skipping Python dependency updates (-SkipPython)." 'INFO'
}

# -----------------------------
# Update metadata timestamp (optional)
# -----------------------------
try {
  $metaPath = Join-Path $InstallDir "hueyos_install.json"
  if (Test-Path -LiteralPath $metaPath) {
    $m = Get-Content -LiteralPath $metaPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $m.updatedAt = (Get-Date).ToString("o")
    $m.updateLogPath = $LogPath
    $m | ConvertTo-Json -Depth 6 | Out-File -FilePath $metaPath -Encoding UTF8
    Write-Log "Updated metadata timestamp: $metaPath" 'INFO'
  }
} catch {
  Write-Log "Failed to update metadata. Error: $($_.Exception.Message)" 'WARN'
}

Write-Log "Update complete." 'INFO'
Write-Host ""
Write-Host "***********************************************"
Write-Host "  Monkey Head Project / HueyOS updated."
Write-Host "  InstallDir: $InstallDir"
Write-Host "  Log:        $LogPath"
Write-Host "***********************************************"
