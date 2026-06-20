[CmdletBinding()]
param(
    [ValidateSet('Runtime', 'Tests', 'Shell')]
    [string]$Mode = 'Runtime',

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Huey.Paths.ps1')
. (Join-Path $PSScriptRoot 'Huey.Common.ps1')
. (Join-Path $PSScriptRoot 'Huey.Python.ps1')

$repoRoot = Get-HueyRepoRoot -StartPath $PSScriptRoot

switch ($Mode) {
    'Tests' {
        & (Join-Path $PSScriptRoot 'Invoke-HueyTests.ps1') @Arguments
        exit $LASTEXITCODE
    }
    'Shell' {
        Start-Process powershell.exe -WorkingDirectory $repoRoot | Out-Null
        exit 0
    }
    default {
        $python = Resolve-HueyPython -RepoRoot $repoRoot
        $runPy = Join-Path $repoRoot 'run.py'
        $exitCode = Invoke-HueyNativeCommand -Command $python.Command -Arguments ($python.Arguments + @($runPy) + $Arguments) -WorkingDirectory $repoRoot
        exit $exitCode
    }
}
