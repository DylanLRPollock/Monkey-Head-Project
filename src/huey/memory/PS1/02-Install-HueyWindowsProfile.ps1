[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Full', 'Mini', 'Dev', 'Runtime')]
    [string]$Profile
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot '01-Install-HueyWindows.ps1') -Profile $Profile
exit $LASTEXITCODE
