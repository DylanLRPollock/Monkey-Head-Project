<#
Monkey Head Project / HueyOS
Windows Uninstaller (PowerShell)

Primary logic sourced from:
- 03-CLEANUP.bat: remove venv + install directory + optional cleanup actions

This script is intentionally safer than 03-CLEANUP.bat:
- Preserves "memory" by default (moves it out of InstallDir if it lives there)
- Does NOT run destructive Docker prunes by default
- Does NOT uninstall global tools by default

Use -RemoveMemory to delete memory.
Use -PurgeChocolateyDeps -Yes to uninstall only Chocolatey packages that were installed by install.ps1
(recorded in hueyos_choco_deps.json).
#>

[CmdletBinding()]
param(
  # Install directory. If omitted, script will attempt to locate it.
  [string]$InstallDir,

  # Remove memory directory as well.
  [switch]$RemoveMemory,

  # Uninstall Chocolatey packages recorded as installed-by-installer.
  [switch]$PurgeChocolateyDeps,

  # Remove pip cache (best-effort).
  [switch]$PurgePipCache,

  # Remove npm cache (best-effort).
  [switch]$PurgeNpmCache,

  # Perform docker system prune (VERY DESTRUCTIVE; requires -Yes).
  [switch]$DockerPrune,

  # Skip confirmation prompts.
  [switch]$Yes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:ForwardedArguments = @()
foreach ($entry in $PSBoundParameters.GetEnumerator()) {
  $switchName = "-$($entry.Key)"
  $value = $entry.Value

  if ($value -is [switch]) {
    if ($value.IsPresent) { $script:ForwardedArguments += $switchName }
    continue
  }

  if ($value -is [bool]) {
    if ($value) { $script:ForwardedArguments += $switchName }
    continue
  }

  if ($null -ne $value -and -not [string]::IsNullOrWhiteSpace([string]$value)) {
    $script:ForwardedArguments += @($switchName, [string]$value)
  }
}

$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogPath = Join-Path $env:TEMP "HueyOS_uninstall_$Timestamp.log"

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
  $argList = @("-NoProfile","-ExecutionPolicy","Bypass","-File", $PSCommandPath) + $script:ForwardedArguments
  try {
    Start-Process -FilePath "powershell.exe" -Verb RunAs -WorkingDirectory (Get-Location).Path -ArgumentList $argList | Out-Null
    exit 0
  } catch {
    Fail "Unable to elevate. Re-run this script from an Administrator PowerShell session."
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
  foreach ($c in $candidates) {
    if (Test-Path -LiteralPath $c) { return $c }
  }
  return $null
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
  } catch { return $false }
}

# Resolve install dir
$InstallDir = Find-InstallDir -Explicit $InstallDir
if (-not $InstallDir) { Fail "Could not locate an installation. Provide -InstallDir explicitly." }
if (-not (Test-Path -LiteralPath $InstallDir)) { Fail "InstallDir not found: $InstallDir" }

$meta = Load-Metadata -Dir $InstallDir
$memoryPath = $null
if ($meta -and $meta.memoryPath) { $memoryPath = [string]$meta.memoryPath }
if ([string]::IsNullOrWhiteSpace($memoryPath)) { $memoryPath = Join-Path $InstallDir "memory" }

# Load recorded Chocolatey deps installed-by-installer (if available) BEFORE deleting InstallDir
$recordedChocoDeps = @()
try {
  if ($meta -and $meta.chocoPackagesInstalled) { $recordedChocoDeps = @($meta.chocoPackagesInstalled) }
} catch { }
if (-not $recordedChocoDeps -or $recordedChocoDeps.Count -eq 0) {
  $depsFile = Join-Path $InstallDir "hueyos_choco_deps.json"
  if (Test-Path -LiteralPath $depsFile) {
    try { $recordedChocoDeps = @(Get-Content -LiteralPath $depsFile -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { }
  }
}

Write-Log "InstallDir : $InstallDir" 'INFO'
Write-Log "MemoryPath : $memoryPath" 'INFO'
Write-Log "Log       : $LogPath" 'INFO'

# Elevation if installed under Program Files
$needsAdmin = $false
try {
  $pf = [IO.Path]::GetFullPath($env:ProgramFiles.TrimEnd('\') + '\')
  $id = [IO.Path]::GetFullPath($InstallDir.TrimEnd('\') + '\')
  if ($id.StartsWith($pf, [System.StringComparison]::OrdinalIgnoreCase)) { $needsAdmin = $true }
} catch { }
if ($PurgeChocolateyDeps -or $DockerPrune) { $needsAdmin = $true }

Ensure-ElevationIfNeeded -NeedsElevation:$needsAdmin

if (-not $Yes) {
  Write-Host ""
  Write-Host "This will uninstall Monkey Head Project / HueyOS from:"
  Write-Host "  $InstallDir"
  if ($RemoveMemory) {
    Write-Host "Memory will be DELETED:"
    Write-Host "  $memoryPath"
  } else {
    Write-Host "Memory will be preserved (moved if necessary):"
    Write-Host "  $memoryPath"
  }
  $resp = Read-Host "Proceed? (Y/N)"
  if ($resp -notin @("Y","y","Yes","YES")) {
    Fail "Uninstall cancelled by user." 2
  }
}

# Preserve memory by default (only if it lives under InstallDir)
$backupPath = $null
if (-not $RemoveMemory) {
  if ((Test-Path -LiteralPath $memoryPath) -and (Is-PathUnder -Child $memoryPath -Parent $InstallDir)) {
    $backupRoot = Join-Path $env:LOCALAPPDATA "MonkeyHeadProject"
    $backupPath = Join-Path $backupRoot ("memory_backup_{0}" -f $Timestamp)
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null

    Write-Log "Preserving memory: moving '$memoryPath' -> '$backupPath'" 'INFO'
    try {
      Move-Item -LiteralPath $memoryPath -Destination $backupPath -Force
    } catch {
      # Fallback to copy+delete
      Write-Log "Move failed; attempting copy+remove. Error: $($_.Exception.Message)" 'WARN'
      Copy-Item -LiteralPath $memoryPath -Destination $backupPath -Recurse -Force
      Remove-Item -LiteralPath $memoryPath -Recurse -Force
    }
  } else {
    Write-Log "Memory path is outside InstallDir or not present; leaving as-is." 'INFO'
  }
}

# Remove install directory
Write-Log "Removing install directory: $InstallDir" 'WARN'
try {
  Remove-Item -LiteralPath $InstallDir -Recurse -Force
} catch {
  Fail "Failed to remove install directory. Error: $($_.Exception.Message)"
}

# Remove memory (if requested) - if memory is outside install dir, this will delete it.
if ($RemoveMemory) {
  if (Test-Path -LiteralPath $memoryPath) {
    Write-Log "Removing memory directory: $memoryPath" 'WARN'
    try {
      Remove-Item -LiteralPath $memoryPath -Recurse -Force
    } catch {
      Fail "Failed to remove memory directory. Error: $($_.Exception.Message)"
    }
  } else {
    Write-Log "Memory directory not found; nothing to remove." 'INFO'
  }
}

# Optional caches
if ($PurgePipCache -and (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Log "Purging pip cache (best-effort)..." 'INFO'
  try { Invoke-Native -Exe "python" -Args @("-m","pip","cache","purge") -AllowNonZero } catch { }
}
if ($PurgeNpmCache -and (Get-Command npm -ErrorAction SilentlyContinue)) {
  Write-Log "Purging npm cache (best-effort)..." 'INFO'
  try { Invoke-Native -Exe "npm" -Args @("cache","clean","--force") -AllowNonZero } catch { }
}

# VERY destructive docker prune (off by default)
if ($DockerPrune) {
  if (-not $Yes) {
    Fail "-DockerPrune requires -Yes because it is destructive (removes images/volumes)."
  }
  if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Log "Running docker system prune -a -f --volumes (DESTRUCTIVE)..." 'WARN'
    try { Invoke-Native -Exe "docker" -Args @("system","prune","-a","-f","--volumes") -AllowNonZero } catch { }
  } else {
    Write-Log "docker not found; skipping docker prune." 'WARN'
  }
}

# Purge Chocolatey deps installed by installer
if ($PurgeChocolateyDeps) {
  if (-not $Yes) {
    Fail "-PurgeChocolateyDeps requires -Yes (explicit confirmation)."
  }

  if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Log "Chocolatey not found; cannot purge deps." 'WARN'
  } else {
    if (-not $recordedChocoDeps -or $recordedChocoDeps.Count -eq 0) {
      Write-Log "No recorded Chocolatey packages to purge (metadata missing or empty)." 'INFO'
    } else {
      foreach ($pkg in $recordedChocoDeps) {
        if ([string]::IsNullOrWhiteSpace($pkg)) { continue }
        Write-Log "Uninstalling Chocolatey package (recorded): $pkg" 'WARN'
        try { Invoke-Native -Exe "choco" -Args @("uninstall","-y",$pkg,"--no-progress") -AllowNonZero } catch { }
      }
    }
  }
}

Write-Log "Uninstall complete." 'INFO'
Write-Host ""
Write-Host "***********************************************"
Write-Host "  Monkey Head Project / HueyOS uninstalled."
if ($backupPath) {
  Write-Host "  Memory preserved at:"
  Write-Host "    $backupPath"
} elseif (-not $RemoveMemory) {
  Write-Host "  Memory was left in-place:"
  Write-Host "    $memoryPath"
} else {
  Write-Host "  Memory removed."
}
Write-Host "  Log: $LogPath"
Write-Host "***********************************************"
