REM Monkey Head Project
REM By: Dylan L.R. Pollock
REM www.dlrp.ca
REM HueyOS: Run batch script (huey/memory/BAT)

@echo off
REM ==================================================
REM This file is a part of the 'Monkey Head Project'
REM Website:   https://dlrp.ca
REM GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
REM License:   https://opensource.org/license/gpl-3-0
REM Overseen By:   Dylan L.R. Pollock
REM Updated: 06.11.2025
REM ==================================================
REM This script launches the app using the virtual environment
setlocal
set "SCRIPT_DIR=%~dp0"
set "ACTIVATE=%SCRIPT_DIR%venv\Scripts\activate.bat"

if /I "%~1"=="help"       goto :help
if /I "%~1"=="--help"     goto :help
if /I "%~1"=="/?"         goto :help
if /I "%~1"=="tests"      goto :tests
if /I "%~1"=="--tests"    goto :tests

:run
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
goto :eof

:tests
pushd "%SCRIPT_DIR%"
if not exist "%ACTIVATE%" (
    echo Virtual environment not found. Please run install.bat first.
    popd
    endlocal
    exit /b 1
)
call "%ACTIVATE%"
call "%SCRIPT_DIR%run-tests.bat"
popd
endlocal
goto :eof

:help
echo Usage: run.bat [options]
echo.
echo Options passed after run.bat are forwarded to run.py.
echo Common examples:
echo    --cli --minimal --simple-chat --module mod[:func]
echo    --system-check --version
echo Additional commands:
echo    tests   Run the project's test suite.
echo    help    Display this help text.
endlocal
