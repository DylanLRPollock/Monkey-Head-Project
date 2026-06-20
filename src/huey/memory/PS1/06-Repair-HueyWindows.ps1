[CmdletBinding()]
param(
    [ValidateSet('Full', 'Mini', 'Dev', 'Runtime')]
    [string]$Profile = 'Full'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot '01-Install-HueyWindows.ps1') -Profile $Profile -RecreateVenv
exit $LASTEXITCODE
