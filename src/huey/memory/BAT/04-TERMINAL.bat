@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "TEMPLATE=%SCRIPT_DIR%terminal-settings.json"
set "SETTINGS_DIR=%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState"
set "SETTINGS_FILE=%SETTINGS_DIR%\settings.json"
set "INSTALL_TERMINAL=0"
set "BACKUP_SETTINGS=0"
set "APPLY_TEMPLATE=0"
set "RESTORE_FILE="

:parse_args
if "%~1"=="" goto :args_done
if /I "%~1"=="help" goto :usage
if /I "%~1"=="--help" goto :usage
if /I "%~1"=="/?" goto :usage
if /I "%~1"=="--install" (
    set "INSTALL_TERMINAL=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--backup" (
    set "BACKUP_SETTINGS=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--apply" (
    set "APPLY_TEMPLATE=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--restore" (
    if "%~2"=="" (
        echo [ERROR] --restore requires a file path.
        exit /b 2
    )
    set "RESTORE_FILE=%~2"
    shift
    shift
    goto :parse_args
)
if /I "%~1"=="--template" (
    if "%~2"=="" (
        echo [ERROR] --template requires a file path.
        exit /b 2
    )
    set "TEMPLATE=%~2"
    shift
    shift
    goto :parse_args
)
echo [ERROR] Unknown argument: %~1
goto :usage

:args_done
where wt >nul 2>&1
if errorlevel 1 (
    if "%INSTALL_TERMINAL%"=="1" (
        winget install --id Microsoft.WindowsTerminal -e --source winget --accept-source-agreements --accept-package-agreements
        if errorlevel 1 exit /b 1
    ) else (
        echo [INFO] Windows Terminal is not currently available on PATH.
    )
) else (
    echo [INFO] Windows Terminal is available.
)

if not exist "%SETTINGS_DIR%" mkdir "%SETTINGS_DIR%" >nul 2>&1

if "%BACKUP_SETTINGS%"=="1" if exist "%SETTINGS_FILE%" (
    call "%SCRIPT_DIR%_common.bat" :timestamp BACKUP_STAMP
    copy /Y "%SETTINGS_FILE%" "%SETTINGS_DIR%\settings.backup.%BACKUP_STAMP%.json" >nul
    if errorlevel 1 exit /b 1
    echo Backed up current settings to "%SETTINGS_DIR%\settings.backup.%BACKUP_STAMP%.json"
)

if defined RESTORE_FILE (
    if not exist "%RESTORE_FILE%" (
        echo [ERROR] Restore file not found: "%RESTORE_FILE%"
        exit /b 1
    )
    copy /Y "%RESTORE_FILE%" "%SETTINGS_FILE%" >nul
    if errorlevel 1 exit /b 1
    echo Restored terminal settings from "%RESTORE_FILE%"
)

if "%APPLY_TEMPLATE%"=="1" (
    if not exist "%TEMPLATE%" (
        echo [ERROR] Terminal settings template not found: "%TEMPLATE%"
        exit /b 1
    )
    copy /Y "%TEMPLATE%" "%SETTINGS_FILE%" >nul
    if errorlevel 1 exit /b 1
    echo Applied terminal settings from "%TEMPLATE%"
)

if "%INSTALL_TERMINAL%"=="0" if "%BACKUP_SETTINGS%"=="0" if "%APPLY_TEMPLATE%"=="0" if not defined RESTORE_FILE (
    echo Settings path: "%SETTINGS_FILE%"
    if exist "%TEMPLATE%" (
        echo Template path: "%TEMPLATE%"
    ) else (
        echo Template path not found. Create "%TEMPLATE%" and re-run with --apply if you want to manage settings from this folder.
    )
)

exit /b 0

:usage
echo Usage: %~nx0 [options]
echo.
echo Options:
echo   --install              Install Windows Terminal with winget when it is missing.
echo   --backup               Back up the current settings.json file.
echo   --apply                Apply the template file next to this script.
echo   --restore FILE         Restore a previously backed-up settings file.
echo   --template FILE        Override the template path used by --apply.
exit /b 0
