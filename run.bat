@echo off
REM ==================================================
REM This file is a part of the 'Monkey Head Project'
REM Website:   https://dlrp.ca
REM GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
REM License:   https://opensource.org/license/gpl-3-0
REM Overseen By:   Dylan L.R. Pollock
REM Updated: 06.05.2025
REM ==================================================
REM This script launches the app using the virtual environment
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
python run.py %*
popd
endlocal
