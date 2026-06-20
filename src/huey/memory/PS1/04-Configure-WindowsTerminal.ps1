[CmdletBinding()]
param(
    [switch]$Install,
    [switch]$Backup,
    [switch]$Apply,
    [string]$RestoreFile,
    [string]$TemplatePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Huey.Paths.ps1')
. (Join-Path $PSScriptRoot 'Huey.Common.ps1')

$repoRoot = Get-HueyRepoRoot -StartPath $PSScriptRoot
$logPath = New-HueyLogFile -Name 'powershell-terminal' -RepoRoot $repoRoot
$settingsDirectory = Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState'
$settingsFile = Join-Path $settingsDirectory 'settings.json'

if ([string]::IsNullOrWhiteSpace($TemplatePath)) {
    $TemplatePath = Join-Path $PSScriptRoot 'terminal-settings.json'
}

if (-not (Test-HueyCommand -Name 'wt')) {
    if ($Install) {
        if (-not (Test-HueyCommand -Name 'winget')) {
            throw 'winget is not available.'
        }
        Invoke-HueyNativeCommand -Command 'winget' -Arguments @('install', '--id', 'Microsoft.WindowsTerminal', '-e', '--source', 'winget', '--accept-source-agreements', '--accept-package-agreements') -WorkingDirectory $repoRoot -LogPath $logPath
    } else {
        Write-HueyLog -Message 'Windows Terminal is not currently on PATH.' -Level WARN -LogPath $logPath
    }
}

if (-not (Test-Path -LiteralPath $settingsDirectory)) {
    New-Item -ItemType Directory -Path $settingsDirectory -Force | Out-Null
}

if ($Backup -and (Test-Path -LiteralPath $settingsFile)) {
    $backupPath = Join-Path $settingsDirectory ("settings.backup.{0}.json" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
    Copy-Item -LiteralPath $settingsFile -Destination $backupPath -Force
    Write-HueyLog -Message "Backed up terminal settings to $backupPath" -LogPath $logPath
}

if (-not [string]::IsNullOrWhiteSpace($RestoreFile)) {
    if (-not (Test-Path -LiteralPath $RestoreFile -PathType Leaf)) {
        throw "Restore file not found: $RestoreFile"
    }
    Copy-Item -LiteralPath $RestoreFile -Destination $settingsFile -Force
    Write-HueyLog -Message "Restored terminal settings from $RestoreFile" -LogPath $logPath
}

if ($Apply) {
    if (-not (Test-Path -LiteralPath $TemplatePath -PathType Leaf)) {
        throw "Template file not found: $TemplatePath"
    }
    Copy-Item -LiteralPath $TemplatePath -Destination $settingsFile -Force
    Write-HueyLog -Message "Applied terminal settings from $TemplatePath" -LogPath $logPath
}

if (-not $Install -and -not $Backup -and -not $Apply -and [string]::IsNullOrWhiteSpace($RestoreFile)) {
    Write-HueyLog -Message "Terminal settings path: $settingsFile" -LogPath $logPath
    if (Test-Path -LiteralPath $TemplatePath -PathType Leaf) {
        Write-HueyLog -Message "Template path: $TemplatePath" -LogPath $logPath
    } else {
        Write-HueyLog -Message "No terminal template found at $TemplatePath" -Level WARN -LogPath $logPath
    }
}
