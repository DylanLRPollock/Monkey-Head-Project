Set-StrictMode -Version Latest

function Get-HueyAutomationRepoRoot {
    [CmdletBinding()]
    param(
        [string]$StartPath = $PSScriptRoot
    )

    $item = Get-Item -LiteralPath $StartPath -ErrorAction Stop
    $directory = if ($item -is [System.IO.FileInfo]) { $item.Directory } else { [System.IO.DirectoryInfo]$item }

    while ($null -ne $directory) {
        if (
            (Test-Path -LiteralPath (Join-Path $directory.FullName 'pyproject.toml') -PathType Leaf) -and
            (Test-Path -LiteralPath (Join-Path $directory.FullName 'run.py') -PathType Leaf)
        ) {
            return $directory.FullName
        }

        $directory = $directory.Parent
    }

    throw "Could not locate the Huey repository root from '$StartPath'."
}

function Invoke-HueyMemoryPs1 {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptName,

        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments = @()
    )

    $repoRoot = Get-HueyAutomationRepoRoot -StartPath $PSScriptRoot
    $target = Join-Path $repoRoot "src\huey\memory\PS1\$ScriptName"
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
        throw "Remembered PowerShell script not found: $target"
    }

    & $target @Arguments
    $exitCode = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
    exit $exitCode
}
