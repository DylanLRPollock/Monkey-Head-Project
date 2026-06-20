Set-StrictMode -Version Latest

function Assert-HueyProjectPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [string]$RepoRoot = (Get-HueyRepoRoot -StartPath $PSScriptRoot)
    )

    $resolvedPath = [System.IO.Path]::GetFullPath($Path)
    $resolvedRoot = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot '.'))

    if (-not $resolvedPath.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path '$Path' is outside the repository root '$RepoRoot'."
    }

    return $resolvedPath
}

function Confirm-HueyAction {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,

        [switch]$Force
    )

    if ($Force) {
        return $true
    }

    $response = Read-Host "$Message [y/N]"
    return $response -in @('y', 'Y', 'yes', 'YES')
}
