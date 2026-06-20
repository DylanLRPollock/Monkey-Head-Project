@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "COMMAND=%~1"
if not defined COMMAND set "COMMAND=docker"

if /I "%COMMAND%"=="help" goto :usage
if /I "%COMMAND%"=="--help" goto :usage
if /I "%COMMAND%"=="/?" goto :usage

if /I "%COMMAND%"=="docker" (
    shift
    call "%SCRIPT_DIR%07-CONTAINER.bat" down %*
    exit /b %errorlevel%
)

if /I "%COMMAND%"=="minikube" (
    where minikube >nul 2>&1
    if errorlevel 1 (
        echo [WARN] minikube is not available.
        exit /b 0
    )
    minikube stop
    exit /b %errorlevel%
)

if /I "%COMMAND%"=="all" (
    call "%SCRIPT_DIR%07-CONTAINER.bat" down
    if errorlevel 1 exit /b %errorlevel%
    where minikube >nul 2>&1
    if not errorlevel 1 minikube stop
    exit /b 0
)

echo [ERROR] Unknown stop command: %COMMAND%
goto :usage

:usage
echo Usage: %~nx0 [docker^|minikube^|all] [extra args]
echo.
echo This helper only stops project-scoped services. It never stops or removes all Docker containers globally.
exit /b 0
