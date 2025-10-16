REM Monkey Head Project
REM By: Dylan L.R. Pollock
REM www.dlrp.ca
REM HueyOS: Run Tests batch script (huey/memory/BAT)

@echo off
REM ==================================================
REM This file is a part of the 'Monkey Head Project'
REM Website:   https://dlrp.ca
REM GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
REM License:   https://opensource.org/license/gpl-3-0
REM Overseen By:   Dylan L.R. Pollock
REM Updated: 06.11.2025
REM ==================================================
REM This script runs the project's tests using the virtual environment
setlocal
set "SCRIPT_DIR=%~dp0"
set "ACTIVATE=%SCRIPT_DIR%venv\Scripts\activate.bat"

pushd "%SCRIPT_DIR%"
if not exist "%ACTIVATE%" (
    echo Virtual environment not found. Please run install.bat first.
    popd
    endlocal
    exit /b 1
)
call "%ACTIVATE%"
if not exist memory\LOGS mkdir memory\LOGS
set "LOG_FILE=memory\LOGS\test_results.log"
echo Test run started at %DATE% %TIME% > "%LOG_FILE%"
pytest -vv --cov=monkey_head --cov-report=term >> "%LOG_FILE%" 2>&1
popd
endlocal

