Set-StrictMode -Version Latest

function Resolve-HueyComposeCommand {
    [CmdletBinding()]
    param()

    if (Test-HueyCommand -Name 'docker') {
        try {
            & docker compose version *> $null
            if ($LASTEXITCODE -eq 0) {
                return [pscustomobject]@{
                    Command = 'docker'
                    Arguments = @('compose')
                }
            }
        }
        catch {
        }
    }

    if (Test-HueyCommand -Name 'docker-compose') {
        return [pscustomobject]@{
            Command = 'docker-compose'
            Arguments = @()
        }
    }

    throw 'Neither docker compose nor docker-compose is available.'
}

function Get-HueyDockerProjectName {
    [CmdletBinding()]
    param()

    return 'hueyos'
}

function Invoke-HueyCompose {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [string]$RepoRoot = (Get-HueyRepoRoot -StartPath $PSScriptRoot),

        [string]$LogPath
    )

    $composeFile = Get-HueyComposeFile -RepoRoot $RepoRoot
    if (-not (Test-Path -LiteralPath $composeFile)) {
        throw "Docker Compose file not found at '$composeFile'."
    }

    $compose = Resolve-HueyComposeCommand
    $baseArguments = $compose.Arguments + @('-p', (Get-HueyDockerProjectName), '-f', $composeFile)

    return (Invoke-HueyNativeCommand -Command $compose.Command -Arguments ($baseArguments + $Arguments) -WorkingDirectory $RepoRoot -LogPath $LogPath)
}
