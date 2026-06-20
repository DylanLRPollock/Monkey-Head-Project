@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
if /I "%~1"=="help" (
    echo Usage: %~nx0 [install options]
    echo.
    call "%SCRIPT_DIR%install.bat" --help
    exit /b %errorlevel%
)
if /I "%~1"=="--help" (
    echo Usage: %~nx0 [install options]
    echo.
    call "%SCRIPT_DIR%install.bat" --help
    exit /b %errorlevel%
)
if /I "%~1"=="/?" (
    echo Usage: %~nx0 [install options]
    echo.
    call "%SCRIPT_DIR%install.bat" --help
    exit /b %errorlevel%
)
call "%SCRIPT_DIR%install.bat" --profile mini %*
exit /b %errorlevel%
