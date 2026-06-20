@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "COMMAND=%~1"
if not defined COMMAND set "COMMAND=ps"

if /I "%COMMAND%"=="help" goto :usage
if /I "%COMMAND%"=="--help" goto :usage
if /I "%COMMAND%"=="/?" goto :usage

call "%SCRIPT_DIR%_common.bat" :resolve_repo_root ROOT_DIR "%SCRIPT_DIR%"
if errorlevel 1 (
    echo [ERROR] Could not locate the repository root from "%SCRIPT_DIR%".
    exit /b 1
)

set "COMPOSE_FILE=%ROOT_DIR%\infra\docker\docker-compose.yml"
set "PROJECT_NAME=hueyos"

if /I "%COMMAND%"=="up" (
    shift
    call "%SCRIPT_DIR%_common.bat" :compose "%COMPOSE_FILE%" "%PROJECT_NAME%" up -d %*
    exit /b %errorlevel%
)
if /I "%COMMAND%"=="down" (
    shift
    call "%SCRIPT_DIR%_common.bat" :compose "%COMPOSE_FILE%" "%PROJECT_NAME%" down %*
    exit /b %errorlevel%
)
if /I "%COMMAND%"=="ps" (
    shift
    call "%SCRIPT_DIR%_common.bat" :compose "%COMPOSE_FILE%" "%PROJECT_NAME%" ps %*
    exit /b %errorlevel%
)
if /I "%COMMAND%"=="logs" (
    shift
    call "%SCRIPT_DIR%_common.bat" :compose "%COMPOSE_FILE%" "%PROJECT_NAME%" logs --tail 200 %*
    exit /b %errorlevel%
)
if /I "%COMMAND%"=="build" (
    shift
    call "%SCRIPT_DIR%_common.bat" :compose "%COMPOSE_FILE%" "%PROJECT_NAME%" build %*
    exit /b %errorlevel%
)
if /I "%COMMAND%"=="pull" (
    shift
    call "%SCRIPT_DIR%_common.bat" :compose "%COMPOSE_FILE%" "%PROJECT_NAME%" pull %*
    exit /b %errorlevel%
)
if /I "%COMMAND%"=="config" (
    shift
    call "%SCRIPT_DIR%_common.bat" :compose "%COMPOSE_FILE%" "%PROJECT_NAME%" config %*
    exit /b %errorlevel%
)

echo [ERROR] Unknown Docker command: %COMMAND%
goto :usage

:usage
echo Usage: %~nx0 [up^|down^|ps^|logs^|build^|pull^|config] [docker compose args]
echo.
echo This helper is scoped to the repo compose file at "infra\docker\docker-compose.yml".
echo Examples:
echo   %~nx0 up --profile worker
echo   %~nx0 logs api
echo   %~nx0 down --volumes
exit /b 0
