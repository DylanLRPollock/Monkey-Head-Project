[CmdletBinding()]
param(
    [ValidateSet('Full', 'Mini', 'Dev', 'Runtime')]
    [string]$Profile = 'Full',

    [switch]$RecreateVenv,
    [switch]$SkipPipUpgrade,
    [switch]$SkipSync,
    [switch]$SkipConnectivity,
    [switch]$SkipPyGPT,
    [switch]$ShowLicenseGui
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Huey.Paths.ps1')
. (Join-Path $PSScriptRoot 'Huey.Common.ps1')
. (Join-Path $PSScriptRoot 'Huey.Python.ps1')

$repoRoot = Get-HueyRepoRoot -StartPath $PSScriptRoot
$logPath = New-HueyLogFile -Name 'powershell-install' -RepoRoot $repoRoot
$logDirectory = Get-HueyLogDirectory -RepoRoot $repoRoot
$rawDirectory = Get-HueyRawDirectory -RepoRoot $repoRoot

if (-not (Test-Path -LiteralPath $logDirectory)) {
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
}
if (-not (Test-Path -LiteralPath $rawDirectory)) {
    New-Item -ItemType Directory -Path $rawDirectory -Force | Out-Null
}

$includePyGPT = ($Profile -in @('Full', 'Dev')) -and (-not $SkipPyGPT)

Write-HueyLog -Message "Preparing local PowerShell install for profile '$Profile'." -LogPath $logPath
$null = New-HueyVenv -RepoRoot $repoRoot -Recreate:$RecreateVenv -LogPath $logPath
$python = Install-HueyRequirements -RepoRoot $repoRoot -UpgradePip:(-not $SkipPipUpgrade) -IncludePyGPT:$includePyGPT -RunSync:(-not $SkipSync) -RunConnectivity:(-not $SkipConnectivity) -LogPath $logPath

if ($ShowLicenseGui) {
    Write-HueyLog -Message 'Attempting to display the license GUI.' -LogPath $logPath
    Push-Location $repoRoot
    try {
        $env:PYTHONPATH = "$repoRoot\src;$($env:PYTHONPATH)"
        & $python.Command @($python.Arguments + @('-c', 'from huey.os.license_gui import show_license_gui; show_license_gui()'))
        if ($LASTEXITCODE -ne 0) {
            Write-HueyLog -Message 'License GUI could not be displayed in this environment.' -Level WARN -LogPath $logPath
        }
    }
    finally {
        Pop-Location
    }
}

Write-HueyLog -Message "PowerShell install complete. Log: $logPath" -LogPath $logPath
