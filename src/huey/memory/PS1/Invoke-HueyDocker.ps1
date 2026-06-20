[CmdletBinding()]
param(
    [ValidateSet('Status', 'Up', 'Down', 'Logs', 'Build', 'Pull', 'Config')]
    [string]$Action = 'Status',

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Huey.Paths.ps1')
. (Join-Path $PSScriptRoot 'Huey.Common.ps1')
. (Join-Path $PSScriptRoot 'Huey.Docker.ps1')

$repoRoot = Get-HueyRepoRoot -StartPath $PSScriptRoot
$logPath = New-HueyLogFile -Name 'powershell-docker' -RepoRoot $repoRoot

$composeArguments = switch ($Action) {
    'Up' { @('up', '-d') + $Arguments; break }
    'Down' { @('down') + $Arguments; break }
    'Logs' { @('logs', '--tail', '200') + $Arguments; break }
    'Build' { @('build') + $Arguments; break }
    'Pull' { @('pull') + $Arguments; break }
    'Config' { @('config') + $Arguments; break }
    default { @('ps') + $Arguments }
}

$exitCode = Invoke-HueyCompose -RepoRoot $repoRoot -Arguments $composeArguments -LogPath $logPath
exit $exitCode
