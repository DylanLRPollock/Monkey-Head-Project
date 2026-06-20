Set-StrictMode -Version Latest

function Resolve-HueySystemPython {
    [CmdletBinding()]
    param()

    if (Test-HueyCommand -Name 'py') {
        return [pscustomobject]@{
            Command = 'py'
            Arguments = @('-3')
            IsVenv = $false
        }
    }

    foreach ($command in @('python', 'python3')) {
        if (Test-HueyCommand -Name $command) {
            return [pscustomobject]@{
                Command = $command
                Arguments = @()
                IsVenv = $false
            }
        }
    }

    throw 'Python was not found on PATH.'
}

function Resolve-HueyPython {
    [CmdletBinding()]
    param(
        [string]$RepoRoot = (Get-HueyRepoRoot -StartPath $PSScriptRoot),

        [switch]$RequireVenv,

        [switch]$PreferSystem
    )

    $venvPython = Get-HueyVenvPython -RepoRoot $RepoRoot
    if ((-not $PreferSystem) -and (Test-Path -LiteralPath $venvPython)) {
        return [pscustomobject]@{
            Command = $venvPython
            Arguments = @()
            IsVenv = $true
        }
    }

    if ($RequireVenv) {
        throw "Local virtual environment not found at '$venvPython'."
    }

    return (Resolve-HueySystemPython)
}

function Test-HueyPythonModule {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Module,

        [string]$RepoRoot = (Get-HueyRepoRoot -StartPath $PSScriptRoot),

        [switch]$RequireVenv
    )

    try {
        $python = Resolve-HueyPython -RepoRoot $RepoRoot -RequireVenv:$RequireVenv
    }
    catch {
        return $false
    }

    Push-Location $RepoRoot
    try {
        & $python.Command @($python.Arguments + @('-c', "import $Module")) *> $null
        return ($LASTEXITCODE -eq 0)
    }
    finally {
        Pop-Location
    }
}

function New-HueyVenv {
    [CmdletBinding()]
    param(
        [string]$RepoRoot = (Get-HueyRepoRoot -StartPath $PSScriptRoot),

        [switch]$Recreate,

        [string]$LogPath
    )

    $venvDirectory = Get-HueyVenvDirectory -RepoRoot $RepoRoot
    $venvPython = Get-HueyVenvPython -RepoRoot $RepoRoot

    if ($Recreate -and (Test-Path -LiteralPath $venvDirectory)) {
        Write-HueyLog -Message "Removing existing virtual environment at '$venvDirectory'." -LogPath $LogPath
        Remove-Item -LiteralPath $venvDirectory -Recurse -Force
    }

    if (-not (Test-Path -LiteralPath $venvPython)) {
        $systemPython = Resolve-HueySystemPython
        Invoke-HueyNativeCommand -Command $systemPython.Command -Arguments ($systemPython.Arguments + @('-m', 'venv', $venvDirectory)) -WorkingDirectory $RepoRoot -LogPath $LogPath
    }

    return (Resolve-HueyPython -RepoRoot $RepoRoot -RequireVenv)
}

function Install-HueyRequirements {
    [CmdletBinding()]
    param(
        [string]$RepoRoot = (Get-HueyRepoRoot -StartPath $PSScriptRoot),

        [switch]$UpgradePip,

        [switch]$IncludePyGPT,

        [switch]$RunSync,

        [switch]$RunConnectivity,

        [string]$LogPath
    )

    $python = Resolve-HueyPython -RepoRoot $RepoRoot -RequireVenv
    $requirements = Join-Path $RepoRoot 'requirements.txt'

    if ($UpgradePip) {
        Invoke-HueyNativeCommand -Command $python.Command -Arguments ($python.Arguments + @('-m', 'pip', 'install', '--upgrade', 'pip')) -WorkingDirectory $RepoRoot -LogPath $LogPath
    }

    if (Test-Path -LiteralPath $requirements) {
        Invoke-HueyNativeCommand -Command $python.Command -Arguments ($python.Arguments + @('-m', 'pip', 'install', '-r', $requirements)) -WorkingDirectory $RepoRoot -LogPath $LogPath
    }

    if ($IncludePyGPT) {
        $pygptPath = Join-Path $RepoRoot 'vendor\pygpt\pygpt-mhp'
        if (Test-Path -LiteralPath $pygptPath) {
            Invoke-HueyNativeCommand -Command $python.Command -Arguments ($python.Arguments + @('-m', 'pip', 'install', '-e', $pygptPath)) -WorkingDirectory $RepoRoot -LogPath $LogPath
        }
    }

    if ($RunSync) {
        $syncScript = Join-Path $RepoRoot 'src\huey\memory\PY\sync_pygpt_structure.py'
        if (Test-Path -LiteralPath $syncScript) {
            Invoke-HueyNativeCommand -Command $python.Command -Arguments ($python.Arguments + @($syncScript)) -WorkingDirectory $RepoRoot -LogPath $LogPath
        }
    }

    if ($RunConnectivity) {
        $connectivityScript = Join-Path $RepoRoot 'scripts\check_inter_program_connectivity.py'
        if (Test-Path -LiteralPath $connectivityScript) {
            Invoke-HueyNativeCommand -Command $python.Command -Arguments ($python.Arguments + @($connectivityScript)) -WorkingDirectory $RepoRoot -LogPath $LogPath
        }
    }

    return $python
}
