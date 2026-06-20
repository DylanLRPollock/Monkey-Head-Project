@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
if /I "%~1"=="help" (
    echo Usage: %~nx0 [cleanup options]
    echo.
    call "%SCRIPT_DIR%03-CLEANUP.bat" --help
    exit /b %errorlevel%
)
if /I "%~1"=="--help" (
    echo Usage: %~nx0 [cleanup options]
    echo.
    call "%SCRIPT_DIR%03-CLEANUP.bat" --help
    exit /b %errorlevel%
)
if /I "%~1"=="/?" (
    echo Usage: %~nx0 [cleanup options]
    echo.
    call "%SCRIPT_DIR%03-CLEANUP.bat" --help
    exit /b %errorlevel%
)
call "%SCRIPT_DIR%03-CLEANUP.bat" %*
exit /b %errorlevel%
