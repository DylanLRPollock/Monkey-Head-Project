@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "COMMAND=%~1"
set "PROJECT_NAME=hueyos"
set "PROJECT_PREFIX=hueyos_"
if not defined COMMAND set "COMMAND=list"

if /I "%COMMAND%"=="help" goto :usage
if /I "%COMMAND%"=="--help" goto :usage
if /I "%COMMAND%"=="/?" goto :usage

where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] docker is not available.
    exit /b 1
)

if /I "%COMMAND%"=="list" (
    docker volume ls --filter label=com.docker.compose.project=%PROJECT_NAME%
    exit /b %errorlevel%
)

if /I "%COMMAND%"=="inspect" (
    if "%~2"=="" (
        echo [ERROR] inspect requires a volume name.
        exit /b 2
    )
    call :normalize_volume_name "%~2" FULL_NAME
    docker volume inspect "%FULL_NAME%"
    exit /b %errorlevel%
)

if /I "%COMMAND%"=="remove" (
    if "%~2"=="" (
        echo [ERROR] remove requires a volume name.
        exit /b 2
    )
    if /I not "%~3"=="--yes" (
        echo [ERROR] remove requires --yes for confirmation.
        exit /b 2
    )
    call :normalize_volume_name "%~2" FULL_NAME
    docker volume rm "%FULL_NAME%"
    exit /b %errorlevel%
)

if /I "%COMMAND%"=="prune" (
    if /I not "%~2"=="--yes" (
        echo [ERROR] prune requires --yes for confirmation.
        exit /b 2
    )
    for /f "delims=" %%V in ('docker volume ls --quiet --filter label=com.docker.compose.project=%PROJECT_NAME%') do (
        docker volume rm "%%V"
        if errorlevel 1 exit /b 1
    )
    exit /b 0
)

if /I "%COMMAND%"=="backup" (
    if "%~2"=="" (
        echo [ERROR] backup requires a volume name.
        exit /b 2
    )
    if "%~3"=="" (
        echo [ERROR] backup requires a destination directory.
        exit /b 2
    )
    call :normalize_volume_name "%~2" FULL_NAME
    set "BACKUP_DIR=%~3"
    if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%" >nul 2>&1
    call "%SCRIPT_DIR%_common.bat" :timestamp BACKUP_STAMP
    set "ARCHIVE_NAME=%FULL_NAME%_%BACKUP_STAMP%.tar.gz"
    docker run --rm -v "%FULL_NAME%:/volume" -v "%BACKUP_DIR%:/backup" alpine sh -c "tar czf /backup/%ARCHIVE_NAME% -C /volume ."
    exit /b %errorlevel%
)

if /I "%COMMAND%"=="restore" (
    if "%~2"=="" (
        echo [ERROR] restore requires a volume name.
        exit /b 2
    )
    if "%~3"=="" (
        echo [ERROR] restore requires an archive path.
        exit /b 2
    )
    if /I not "%~4"=="--yes" (
        echo [ERROR] restore requires --yes for confirmation.
        exit /b 2
    )
    call :normalize_volume_name "%~2" FULL_NAME
    if not exist "%~3" (
        echo [ERROR] Archive not found: "%~3"
        exit /b 1
    )
    for %%I in ("%~3") do (
        set "ARCHIVE_DIR=%%~dpI"
        set "ARCHIVE_FILE=%%~nxI"
    )
    docker run --rm -v "%FULL_NAME%:/volume" -v "%ARCHIVE_DIR%:/backup" alpine sh -c "rm -rf /volume/* && tar xzf /backup/%ARCHIVE_FILE% -C /volume"
    exit /b %errorlevel%
)

echo [ERROR] Unknown volume command: %COMMAND%
goto :usage

:normalize_volume_name
setlocal EnableExtensions
set "name=%~1"
if /I "%name:~0,7%"=="hueyos_" (
    set "full_name=%name%"
) else (
    set "full_name=hueyos_%name%"
)
endlocal & set "%~2=%full_name%" & exit /b 0

:usage
echo Usage: %~nx0 [list^|inspect^|remove^|prune^|backup^|restore] [args]
echo.
echo Commands:
echo   list
echo   inspect VOLUME
echo   remove VOLUME --yes
echo   prune --yes
echo   backup VOLUME DEST_DIR
echo   restore VOLUME ARCHIVE --yes
echo.
echo Volume names are automatically scoped to the "%PROJECT_PREFIX%" project prefix.
exit /b 0
