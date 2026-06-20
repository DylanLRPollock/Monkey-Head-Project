[CmdletBinding()]
param(
    [ValidateSet('Launch', 'Update', 'LaunchAfterUpdate')]
    [string]$Action = 'Launch'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Huey.Paths.ps1')
. (Join-Path $PSScriptRoot 'Huey.Common.ps1')
. (Join-Path $PSScriptRoot 'Huey.Python.ps1')

$repoRoot = Get-HueyRepoRoot -StartPath $PSScriptRoot
$logPath = New-HueyLogFile -Name 'powershell-pygpt' -RepoRoot $repoRoot

if ($Action -in @('Update', 'LaunchAfterUpdate')) {
    $python = Resolve-HueyPython -RepoRoot $repoRoot -RequireVenv
    $pygptPath = Join-Path $repoRoot 'vendor\pygpt\pygpt-mhp'
    if (Test-Path -LiteralPath $pygptPath) {
        Invoke-HueyNativeCommand -Command $python.Command -Arguments ($python.Arguments + @('-m', 'pip', 'install', '-e', $pygptPath)) -WorkingDirectory $repoRoot -LogPath $logPath
        $syncScript = Join-Path $repoRoot 'src\huey\memory\PY\sync_pygpt_structure.py'
        if (Test-Path -LiteralPath $syncScript) {
            Invoke-HueyNativeCommand -Command $python.Command -Arguments ($python.Arguments + @($syncScript)) -WorkingDirectory $repoRoot -LogPath $logPath
        }
    } else {
        Invoke-HueyNativeCommand -Command $python.Command -Arguments ($python.Arguments + @('-m', 'pip', 'install', '--upgrade', 'pygpt-net')) -WorkingDirectory $repoRoot -LogPath $logPath
    }
}

if ($Action -in @('Launch', 'LaunchAfterUpdate')) {
    $python = Resolve-HueyPython -RepoRoot $repoRoot
    Push-Location $repoRoot
    try {
        $env:PYTHONPATH = "$repoRoot\src;$($env:PYTHONPATH)"
        & $python.Command @($python.Arguments + @('-c', 'from huey.pygpt_custom_cli import CustomPyGPT; CustomPyGPT().run_cli()'))
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
    exit $exitCode
}

exit 0
