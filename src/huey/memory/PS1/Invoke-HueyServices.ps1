[CmdletBinding()]
param(
    [ValidateSet('Local', 'Docker', 'All', 'Open')]
    [string]$Mode = 'Local',

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Huey.Common.ps1')

switch ($Mode) {
    'Docker' {
        & (Join-Path $PSScriptRoot 'Invoke-HueyDocker.ps1') -Action Up @Arguments
        exit $LASTEXITCODE
    }
    'All' {
        & (Join-Path $PSScriptRoot 'Invoke-HueyDocker.ps1') -Action Up @Arguments
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        Open-HueyBrowser
        exit 0
    }
    'Open' {
        Open-HueyBrowser
        exit 0
    }
    default {
        & (Join-Path $PSScriptRoot 'Invoke-Huey.ps1') -Mode Runtime @Arguments
        exit $LASTEXITCODE
    }
}
