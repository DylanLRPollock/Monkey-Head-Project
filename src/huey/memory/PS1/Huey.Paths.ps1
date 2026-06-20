Set-StrictMode -Version Latest

function Get-HueyRepoRoot {
    [CmdletBinding()]
    param(
        [string]$StartPath = $PSScriptRoot
    )

    $item = Get-Item -LiteralPath $StartPath -ErrorAction Stop
    $directory = if ($item -is [System.IO.FileInfo]) { $item.Directory } else { [System.IO.DirectoryInfo]$item }

    while ($null -ne $directory) {
        $pyproject = Join-Path $directory.FullName 'pyproject.toml'
        $runPy = Join-Path $directory.FullName 'run.py'
        if ((Test-Path -LiteralPath $pyproject -PathType Leaf) -and (Test-Path -LiteralPath $runPy -PathType Leaf)) {
            return $directory.FullName
        }
        $directory = $directory.Parent
    }

    throw "Could not locate the Huey repository root from '$StartPath'."
}

function Get-HueyPs1Directory {
    [CmdletBinding()]
    param(
        [string]$RepoRoot = (Get-HueyRepoRoot -StartPath $PSScriptRoot)
    )

    return (Join-Path $RepoRoot 'src\huey\memory\PS1')
}

function Get-HueyLogDirectory {
    [CmdletBinding()]
    param(
        [string]$RepoRoot = (Get-HueyRepoRoot -StartPath $PSScriptRoot)
    )

    return (Join-Path $RepoRoot 'src\huey\memory\LOGS')
}

function Get-HueyRawDirectory {
    [CmdletBinding()]
    param(
        [string]$RepoRoot = (Get-HueyRepoRoot -StartPath $PSScriptRoot)
    )

    return (Join-Path $RepoRoot 'src\huey\memory\RAW')
}

function Get-HueyVenvDirectory {
    [CmdletBinding()]
    param(
        [string]$RepoRoot = (Get-HueyRepoRoot -StartPath $PSScriptRoot)
    )

    return (Join-Path $RepoRoot 'venv')
}

function Get-HueyVenvPython {
    [CmdletBinding()]
    param(
        [string]$RepoRoot = (Get-HueyRepoRoot -StartPath $PSScriptRoot)
    )

    return (Join-Path (Get-HueyVenvDirectory -RepoRoot $RepoRoot) 'Scripts\python.exe')
}

function Get-HueyDocsDirectory {
    [CmdletBinding()]
    param(
        [string]$RepoRoot = (Get-HueyRepoRoot -StartPath $PSScriptRoot)
    )

    return (Join-Path $RepoRoot 'docs')
}

function Get-HueyComposeFile {
    [CmdletBinding()]
    param(
        [string]$RepoRoot = (Get-HueyRepoRoot -StartPath $PSScriptRoot)
    )

    return (Join-Path $RepoRoot 'infra\docker\docker-compose.yml')
}
