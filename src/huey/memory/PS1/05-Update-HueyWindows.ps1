[CmdletBinding()]
param(
    [ValidateSet('Full', 'Mini', 'Dev', 'Runtime')]
    [string]$Profile = 'Full',

    [switch]$RecreateVenv,
    [switch]$Pull,
    [switch]$PreviewWinget,
    [switch]$WingetAll,
    [switch]$ChocolateyAll,
    [switch]$DockerImages,
    [switch]$VSCodeExtensions,
    [switch]$PowerShellModules,
    [switch]$Yes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Huey.Paths.ps1')
. (Join-Path $PSScriptRoot 'Huey.Common.ps1')
. (Join-Path $PSScriptRoot 'Huey.Python.ps1')
. (Join-Path $PSScriptRoot 'Huey.Docker.ps1')

$repoRoot = Get-HueyRepoRoot -StartPath $PSScriptRoot
$logPath = New-HueyLogFile -Name 'powershell-update' -RepoRoot $repoRoot

if (($WingetAll -or $ChocolateyAll) -and (-not $Yes)) {
    throw 'Use -Yes to confirm system-wide update actions.'
}

if ($Pull) {
    if (-not (Test-HueyCommand -Name 'git')) {
        throw 'git is not available.'
    }

    $status = & git -C $repoRoot status --porcelain
    if ($LASTEXITCODE -ne 0) {
        throw 'git status failed.'
    }
    if (-not [string]::IsNullOrWhiteSpace(($status | Out-String).Trim())) {
        throw 'The repository has local changes. Commit or stash them before using -Pull.'
    }

    Invoke-HueyNativeCommand -Command 'git' -Arguments @('-C', $repoRoot, 'pull', '--ff-only', '--recurse-submodules') -WorkingDirectory $repoRoot -LogPath $logPath
    Invoke-HueyNativeCommand -Command 'git' -Arguments @('-C', $repoRoot, 'submodule', 'update', '--init', '--recursive') -WorkingDirectory $repoRoot -LogPath $logPath
}

$includePyGPT = $Profile -in @('Full', 'Dev')
$null = New-HueyVenv -RepoRoot $repoRoot -Recreate:$RecreateVenv -LogPath $logPath
$null = Install-HueyRequirements -RepoRoot $repoRoot -UpgradePip -IncludePyGPT:$includePyGPT -RunSync -RunConnectivity -LogPath $logPath

if ($PreviewWinget) {
    if (Test-HueyCommand -Name 'winget') {
        Invoke-HueyNativeCommand -Command 'winget' -Arguments @('upgrade') -WorkingDirectory $repoRoot -LogPath $logPath
    } else {
        Write-HueyLog -Message 'winget is not available.' -Level WARN -LogPath $logPath
    }
}

if ($WingetAll) {
    Invoke-HueyNativeCommand -Command 'winget' -Arguments @('upgrade', '--all', '--accept-source-agreements', '--accept-package-agreements') -WorkingDirectory $repoRoot -LogPath $logPath
}

if ($ChocolateyAll) {
    if (-not (Test-HueyCommand -Name 'choco')) {
        throw 'Chocolatey is not available.'
    }
    Invoke-HueyNativeCommand -Command 'choco' -Arguments @('upgrade', 'chocolatey', '-y', '--no-progress') -WorkingDirectory $repoRoot -LogPath $logPath -AllowNonZero
    Invoke-HueyNativeCommand -Command 'choco' -Arguments @('upgrade', 'all', '-y', '--no-progress') -WorkingDirectory $repoRoot -LogPath $logPath -AllowNonZero
}

if ($DockerImages) {
    Invoke-HueyCompose -RepoRoot $repoRoot -Arguments @('pull') -LogPath $logPath
}

if ($VSCodeExtensions -and (Test-HueyCommand -Name 'code')) {
    $extensions = & code --list-extensions
    foreach ($extension in $extensions) {
        if (-not [string]::IsNullOrWhiteSpace($extension)) {
            & code --install-extension $extension *> $null
        }
    }
}

if ($PowerShellModules) {
    & powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-InstalledModule | ForEach-Object { Update-Module -Name $_.Name -Force }"
    if ($LASTEXITCODE -ne 0) {
        Write-HueyLog -Message 'PowerShell module updates completed with warnings.' -Level WARN -LogPath $logPath
    }
}

Write-HueyLog -Message "PowerShell update complete. Log: $logPath" -LogPath $logPath
