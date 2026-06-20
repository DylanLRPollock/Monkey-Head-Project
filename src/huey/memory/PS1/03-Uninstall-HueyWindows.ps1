[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [switch]$RemoveLogs,
    [switch]$PurgePipCache,
    [switch]$PurgeNpmCache,
    [switch]$DockerPrune,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Huey.Paths.ps1')
. (Join-Path $PSScriptRoot 'Huey.Common.ps1')
. (Join-Path $PSScriptRoot 'Huey.Safety.ps1')
. (Join-Path $PSScriptRoot 'Huey.Python.ps1')

$repoRoot = Get-HueyRepoRoot -StartPath $PSScriptRoot
$logPath = New-HueyLogFile -Name 'powershell-uninstall' -RepoRoot $repoRoot
$venvDirectory = Get-HueyVenvDirectory -RepoRoot $repoRoot
$pytestCache = Join-Path $repoRoot '.pytest_cache'
$ruffCache = Join-Path $repoRoot '.ruff_cache'
$logDirectory = Get-HueyLogDirectory -RepoRoot $repoRoot

foreach ($path in @($venvDirectory, $pytestCache, $ruffCache)) {
    if (Test-Path -LiteralPath $path) {
        $resolvedPath = Assert-HueyProjectPath -Path $path -RepoRoot $repoRoot
        if ($PSCmdlet.ShouldProcess($resolvedPath, 'Remove project artifact')) {
            Remove-Item -LiteralPath $resolvedPath -Recurse -Force
            Write-HueyLog -Message "Removed $resolvedPath" -LogPath $logPath
        }
    }
}

$pycacheDirectories = Get-ChildItem -LiteralPath $repoRoot -Directory -Recurse -Filter '__pycache__' -Force -ErrorAction SilentlyContinue
foreach ($directory in $pycacheDirectories) {
    $resolvedPath = Assert-HueyProjectPath -Path $directory.FullName -RepoRoot $repoRoot
    if ($PSCmdlet.ShouldProcess($resolvedPath, 'Remove Python bytecode directory')) {
        Remove-Item -LiteralPath $resolvedPath -Recurse -Force
    }
}

$pycFiles = Get-ChildItem -LiteralPath $repoRoot -File -Recurse -Filter '*.pyc' -Force -ErrorAction SilentlyContinue
foreach ($file in $pycFiles) {
    $resolvedPath = Assert-HueyProjectPath -Path $file.FullName -RepoRoot $repoRoot
    if ($PSCmdlet.ShouldProcess($resolvedPath, 'Remove Python bytecode file')) {
        Remove-Item -LiteralPath $resolvedPath -Force
    }
}

if ($RemoveLogs -and (Test-Path -LiteralPath $logDirectory)) {
    $resolvedPath = Assert-HueyProjectPath -Path $logDirectory -RepoRoot $repoRoot
    if ($PSCmdlet.ShouldProcess($resolvedPath, 'Remove Huey log directory')) {
        Remove-Item -LiteralPath $resolvedPath -Recurse -Force
    }
}

if ($PurgePipCache) {
    $python = Resolve-HueyPython -RepoRoot $repoRoot
    if ($PSCmdlet.ShouldProcess('pip cache', 'Purge pip cache')) {
        Invoke-HueyNativeCommand -Command $python.Command -Arguments ($python.Arguments + @('-m', 'pip', 'cache', 'purge')) -WorkingDirectory $repoRoot -LogPath $logPath -AllowNonZero
    }
}

if ($PurgeNpmCache -and (Test-HueyCommand -Name 'npm')) {
    if ($PSCmdlet.ShouldProcess('npm cache', 'Purge npm cache')) {
        Invoke-HueyNativeCommand -Command 'npm' -Arguments @('cache', 'clean', '--force') -WorkingDirectory $repoRoot -LogPath $logPath -AllowNonZero
    }
}

if ($DockerPrune) {
    if (-not (Confirm-HueyAction -Message 'Run docker system prune -a --volumes?' -Force:$Force)) {
        Write-HueyLog -Message 'Skipped docker prune.' -Level WARN -LogPath $logPath
    } elseif ($PSCmdlet.ShouldProcess('docker', 'Prune global Docker data')) {
        Invoke-HueyNativeCommand -Command 'docker' -Arguments @('system', 'prune', '-a', '-f', '--volumes') -WorkingDirectory $repoRoot -LogPath $logPath -AllowNonZero
    }
}

Write-HueyLog -Message "PowerShell cleanup complete. Log: $logPath" -LogPath $logPath
