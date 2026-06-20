[CmdletBinding()]
param(
    [switch]$Coverage,
    [switch]$NoCoverage,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Huey.Paths.ps1')
. (Join-Path $PSScriptRoot 'Huey.Common.ps1')
. (Join-Path $PSScriptRoot 'Huey.Python.ps1')

$repoRoot = Get-HueyRepoRoot -StartPath $PSScriptRoot
$logPath = New-HueyLogFile -Name 'powershell-tests' -RepoRoot $repoRoot
$python = Resolve-HueyPython -RepoRoot $repoRoot -RequireVenv

if (-not (Test-HueyPythonModule -RepoRoot $repoRoot -Module 'pytest' -RequireVenv)) {
    throw 'pytest is not installed in the local virtual environment. Run 01-Install-HueyWindows.ps1 first.'
}

$useCoverage = $Coverage -or ((-not $NoCoverage) -and (Test-HueyPythonModule -RepoRoot $repoRoot -Module 'pytest_cov' -RequireVenv))
$pytestArguments = $python.Arguments + @('-m', 'pytest')
if ($useCoverage) {
    $pytestArguments += @('--cov=huey', '--cov-report=term')
}
$pytestArguments += $Arguments

Push-Location $repoRoot
try {
    & $python.Command @pytestArguments 2>&1 | Tee-Object -FilePath $logPath
    $exitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

Write-HueyLog -Message "Test log: $logPath" -LogPath $logPath
exit $exitCode
