[CmdletBinding()]
param(
    [ValidateSet('Tests', 'Docs', 'All', 'Package')]
    [string]$Target = 'Tests',

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Huey.Paths.ps1')
. (Join-Path $PSScriptRoot 'Huey.Common.ps1')
. (Join-Path $PSScriptRoot 'Huey.Python.ps1')

$repoRoot = Get-HueyRepoRoot -StartPath $PSScriptRoot
$logPath = New-HueyLogFile -Name 'powershell-build' -RepoRoot $repoRoot

switch ($Target) {
    'Tests' {
        & (Join-Path $PSScriptRoot 'Invoke-HueyTests.ps1') @Arguments
        exit $LASTEXITCODE
    }
    'Docs' {
        & (Join-Path $PSScriptRoot 'Invoke-HueyDocs.ps1') @Arguments
        exit $LASTEXITCODE
    }
    'All' {
        & (Join-Path $PSScriptRoot 'Invoke-HueyTests.ps1')
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & (Join-Path $PSScriptRoot 'Invoke-HueyDocs.ps1')
        exit $LASTEXITCODE
    }
    'Package' {
        if (-not (Test-HueyPythonModule -RepoRoot $repoRoot -Module 'build')) {
            throw 'The build module is not installed in the active Python environment.'
        }
        $python = Resolve-HueyPython -RepoRoot $repoRoot
        $exitCode = Invoke-HueyNativeCommand -Command $python.Command -Arguments ($python.Arguments + @('-m', 'build') + $Arguments) -WorkingDirectory $repoRoot -LogPath $logPath
        exit $exitCode
    }
}
