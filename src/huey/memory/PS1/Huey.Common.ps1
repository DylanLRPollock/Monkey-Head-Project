Set-StrictMode -Version Latest

function New-HueyLogFile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [string]$RepoRoot = (Get-HueyRepoRoot -StartPath $PSScriptRoot)
    )

    $logDir = Get-HueyLogDirectory -RepoRoot $RepoRoot
    if (-not (Test-Path -LiteralPath $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }

    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    return (Join-Path $logDir ("{0}_{1}.log" -f $Name, $timestamp))
}

function Write-HueyLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,

        [ValidateSet('INFO', 'WARN', 'ERROR', 'DEBUG')]
        [string]$Level = 'INFO',

        [string]$LogPath
    )

    $line = '{0} [{1}] {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Level, $Message
    Write-Host $line

    if (-not [string]::IsNullOrWhiteSpace($LogPath)) {
        Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
    }
}

function Show-HueySection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title
    )

    Write-Host ''
    Write-Host ('==== {0} ====' -f $Title)
}

function Test-HueyCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-HueyNativeCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [string[]]$Arguments = @(),

        [string]$WorkingDirectory = (Get-Location).Path,

        [string]$LogPath,

        [switch]$AllowNonZero
    )

    Write-HueyLog -Message ("Running: {0} {1}" -f $Command, ($Arguments -join ' ')) -Level DEBUG -LogPath $LogPath

    Push-Location $WorkingDirectory
    try {
        & $Command @Arguments
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    if ((-not $AllowNonZero) -and $exitCode -ne 0) {
        throw "Command '$Command' failed with exit code $exitCode."
    }

    return $exitCode
}

function Open-HueyBrowser {
    [CmdletBinding()]
    param(
        [string]$Uri = 'http://127.0.0.1:1995/docs'
    )

    Start-Process $Uri | Out-Null
}
