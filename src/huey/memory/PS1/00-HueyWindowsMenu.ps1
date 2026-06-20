[CmdletBinding()]
param(
    [ValidateSet('Install', 'Mini', 'Update', 'Cleanup', 'Run', 'Tests', 'Docker', 'Start', 'Stop')]
    [string]$Action
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-MenuAction {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SelectedAction
    )

    switch ($SelectedAction) {
        'Install' { & (Join-Path $PSScriptRoot '01-Install-HueyWindows.ps1') -Profile Full }
        'Mini' { & (Join-Path $PSScriptRoot '01-Install-HueyWindows.ps1') -Profile Mini }
        'Update' { & (Join-Path $PSScriptRoot '05-Update-HueyWindows.ps1') }
        'Cleanup' { & (Join-Path $PSScriptRoot '03-Uninstall-HueyWindows.ps1') -WhatIf }
        'Run' { & (Join-Path $PSScriptRoot 'Invoke-Huey.ps1') }
        'Tests' { & (Join-Path $PSScriptRoot 'Invoke-HueyTests.ps1') }
        'Docker' { & (Join-Path $PSScriptRoot 'Invoke-HueyDocker.ps1') -Action Status }
        'Start' { & (Join-Path $PSScriptRoot 'Invoke-HueyServices.ps1') -Mode All }
        'Stop' { & (Join-Path $PSScriptRoot 'Stop-HueyServices.ps1') -Mode All }
    }

    exit $LASTEXITCODE
}

if ($PSBoundParameters.ContainsKey('Action')) {
    Invoke-MenuAction -SelectedAction $Action
}

while ($true) {
    Write-Host ''
    Write-Host 'Huey Windows PowerShell menu'
    Write-Host '1. Full local setup'
    Write-Host '2. Minimal local setup'
    Write-Host '3. Update local environment'
    Write-Host '4. Preview cleanup'
    Write-Host '5. Run Huey'
    Write-Host '6. Run tests'
    Write-Host '7. Docker status'
    Write-Host '8. Start services'
    Write-Host '9. Stop services'
    Write-Host 'Q. Quit'
    $choice = Read-Host 'Select an option'

    switch ($choice.ToUpperInvariant()) {
        '1' { Invoke-MenuAction -SelectedAction Install }
        '2' { Invoke-MenuAction -SelectedAction Mini }
        '3' { Invoke-MenuAction -SelectedAction Update }
        '4' { Invoke-MenuAction -SelectedAction Cleanup }
        '5' { Invoke-MenuAction -SelectedAction Run }
        '6' { Invoke-MenuAction -SelectedAction Tests }
        '7' { Invoke-MenuAction -SelectedAction Docker }
        '8' { Invoke-MenuAction -SelectedAction Start }
        '9' { Invoke-MenuAction -SelectedAction Stop }
        'Q' { exit 0 }
        default { Write-Warning 'Invalid selection.' }
    }
}
