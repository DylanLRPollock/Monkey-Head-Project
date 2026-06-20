[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InputFile,

    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,

    [string]$Bitrate = '320k'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    throw 'ffmpeg is not available on PATH.'
}

if (-not (Test-Path -LiteralPath $InputFile -PathType Leaf)) {
    throw "Input file not found: $InputFile"
}

if (-not (Test-Path -LiteralPath $OutputDirectory)) {
    New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
}

$outputFile = Join-Path $OutputDirectory ("{0}.mp3" -f [System.IO.Path]::GetFileNameWithoutExtension($InputFile))
& ffmpeg -y -i $InputFile -vn -c:a libmp3lame -b:a $Bitrate $outputFile
exit $LASTEXITCODE
