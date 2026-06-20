[CmdletBinding()]
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments = @())
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_dispatch.ps1')
Invoke-HueyMemoryPs1 -ScriptName 'Invoke-Huey.ps1' @Arguments
