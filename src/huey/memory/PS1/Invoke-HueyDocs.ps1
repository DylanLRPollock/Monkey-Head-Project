[CmdletBinding()]
param(
    [string]$Builder = 'html'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Huey.Paths.ps1')
. (Join-Path $PSScriptRoot 'Huey.Common.ps1')
. (Join-Path $PSScriptRoot 'Huey.Python.ps1')

$repoRoot = Get-HueyRepoRoot -StartPath $PSScriptRoot
$docsDirectory = Get-HueyDocsDirectory -RepoRoot $repoRoot
$buildDirectory = Join-Path $docsDirectory '_build'
$logPath = New-HueyLogFile -Name 'powershell-docs' -RepoRoot $repoRoot
$python = Resolve-HueyPython -RepoRoot $repoRoot

if (-not (Test-HueyPythonModule -RepoRoot $repoRoot -Module 'sphinx')) {
    throw 'Sphinx is not installed in the active Python environment.'
}

$exitCode = Invoke-HueyNativeCommand -Command $python.Command -Arguments ($python.Arguments + @('-m', 'sphinx', '-M', $Builder, $docsDirectory, $buildDirectory)) -WorkingDirectory $docsDirectory -LogPath $logPath
exit $exitCode
