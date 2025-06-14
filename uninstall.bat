@echo off
REM ==================================================
REM This file is a part of the 'Monkey Head Project'
REM Website:   https://dlrp.ca
REM GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
REM License:   https://opensource.org/license/gpl-3-0
REM Overseen By:   Dylan L.R. Pollock
REM Updated: 06.09.2025
REM ==================================================

setlocal
set "SCRIPT_DIR=%~dp0"
set "UNINSTALL_SCRIPT=%SCRIPT_DIR%setup\Windows11\03-CLEANUP.bat"

pushd "%SCRIPT_DIR%"
if not exist "%UNINSTALL_SCRIPT%" (
    echo Uninstallation script not found: %UNINSTALL_SCRIPT%
    popd
    endlocal
    exit /b 1
)
call "%UNINSTALL_SCRIPT%"
popd
endlocal
