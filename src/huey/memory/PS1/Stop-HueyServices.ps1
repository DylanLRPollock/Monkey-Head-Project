[CmdletBinding()]
param(
    [ValidateSet('Docker', 'All', 'Minikube')]
    [string]$Mode = 'Docker',

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Huey.Common.ps1')

switch ($Mode) {
    'Minikube' {
        if (-not (Test-HueyCommand -Name 'minikube')) {
            Write-HueyLog -Message 'minikube is not available.' -Level WARN
            exit 0
        }
        & minikube stop
        exit $LASTEXITCODE
    }
    'All' {
        & (Join-Path $PSScriptRoot 'Invoke-HueyDocker.ps1') -Action Down @Arguments
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        if (Test-HueyCommand -Name 'minikube') {
            & minikube stop
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        }
        exit 0
    }
    default {
        & (Join-Path $PSScriptRoot 'Invoke-HueyDocker.ps1') -Action Down @Arguments
        exit $LASTEXITCODE
    }
}
