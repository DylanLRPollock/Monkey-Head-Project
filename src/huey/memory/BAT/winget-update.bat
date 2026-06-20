@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
if /I "%~1"=="help" (
    echo Usage: %~nx0 [--yes]
    echo.
    echo Without arguments this previews available winget upgrades.
    echo Pass --yes to install all available winget upgrades.
    exit /b 0
)
if /I "%~1"=="--help" (
    echo Usage: %~nx0 [--yes]
    echo.
    echo Without arguments this previews available winget upgrades.
    echo Pass --yes to install all available winget upgrades.
    exit /b 0
)
if /I "%~1"=="/?" (
    echo Usage: %~nx0 [--yes]
    echo.
    echo Without arguments this previews available winget upgrades.
    echo Pass --yes to install all available winget upgrades.
    exit /b 0
)
if /I "%~1"=="--yes" (
    call "%SCRIPT_DIR%05-UPDATE.bat" --winget-all --yes
    exit /b %errorlevel%
)

call "%SCRIPT_DIR%05-UPDATE.bat" --preview-winget
exit /b %errorlevel%
