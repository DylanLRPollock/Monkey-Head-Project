@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "COMMAND=%~1"
if not defined COMMAND set "COMMAND=app"

if /I "%COMMAND%"=="help" goto :usage
if /I "%COMMAND%"=="--help" goto :usage
if /I "%COMMAND%"=="/?" goto :usage

if /I "%COMMAND%"=="app" (
    shift
    call "%SCRIPT_DIR%run.bat" %*
    exit /b %errorlevel%
)

if /I "%COMMAND%"=="docker" (
    shift
    call "%SCRIPT_DIR%07-CONTAINER.bat" up %*
    exit /b %errorlevel%
)

if /I "%COMMAND%"=="all" (
    shift
    call "%SCRIPT_DIR%07-CONTAINER.bat" up %*
    if errorlevel 1 exit /b %errorlevel%
    start "" "http://127.0.0.1:1995/docs"
    exit /b 0
)

if /I "%COMMAND%"=="open" (
    start "" "http://127.0.0.1:1995/docs"
    exit /b 0
)

echo [ERROR] Unknown start command: %COMMAND%
goto :usage

:usage
echo Usage: %~nx0 [app^|docker^|all^|open] [extra args]
echo.
echo Commands:
echo   app      Run the local Python entry point.
echo   docker   Start the Docker Compose stack.
echo   all      Start the Docker Compose stack and open the local docs URL.
echo   open     Open the local docs URL in the default browser.
exit /b 0
