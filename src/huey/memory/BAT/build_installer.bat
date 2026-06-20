@echo off
setlocal EnableExtensions
set "SCRIPT_DIR=%~dp0"
if /I "%~1"=="help" (
    call "%SCRIPT_DIR%06-BUILD.bat" help
    exit /b %errorlevel%
)
if /I "%~1"=="--help" (
    call "%SCRIPT_DIR%06-BUILD.bat" help
    exit /b %errorlevel%
)
if /I "%~1"=="/?" (
    call "%SCRIPT_DIR%06-BUILD.bat" help
    exit /b %errorlevel%
)
call "%SCRIPT_DIR%06-BUILD.bat" installer %*
exit /b %errorlevel%
