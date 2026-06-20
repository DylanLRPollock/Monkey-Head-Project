@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"

if /I "%~1"=="help" goto :usage
if /I "%~1"=="--help" goto :usage
if /I "%~1"=="/?" goto :usage
if /I "%~1"=="install" (
    shift
    call "%SCRIPT_DIR%01-FULL.bat" %*
    exit /b %errorlevel%
)
if /I "%~1"=="mini" (
    shift
    call "%SCRIPT_DIR%02-MINI.bat" %*
    exit /b %errorlevel%
)
if /I "%~1"=="cleanup" (
    shift
    call "%SCRIPT_DIR%03-CLEANUP.bat" %*
    exit /b %errorlevel%
)
if /I "%~1"=="terminal" (
    shift
    call "%SCRIPT_DIR%04-TERMINAL.bat" %*
    exit /b %errorlevel%
)
if /I "%~1"=="update" (
    shift
    call "%SCRIPT_DIR%05-UPDATE.bat" %*
    exit /b %errorlevel%
)
if /I "%~1"=="build" (
    shift
    call "%SCRIPT_DIR%06-BUILD.bat" %*
    exit /b %errorlevel%
)
if /I "%~1"=="docker" (
    shift
    call "%SCRIPT_DIR%07-CONTAINER.bat" %*
    exit /b %errorlevel%
)
if /I "%~1"=="volumes" (
    shift
    call "%SCRIPT_DIR%08-VOLUME.bat" %*
    exit /b %errorlevel%
)
if /I "%~1"=="k8s" (
    shift
    call "%SCRIPT_DIR%09-KUBERNETES.bat" %*
    exit /b %errorlevel%
)
if /I "%~1"=="start" (
    shift
    call "%SCRIPT_DIR%10-START.bat" %*
    exit /b %errorlevel%
)
if /I "%~1"=="run" (
    shift
    call "%SCRIPT_DIR%run.bat" %*
    exit /b %errorlevel%
)
if /I "%~1"=="tests" (
    shift
    call "%SCRIPT_DIR%run-tests.bat" %*
    exit /b %errorlevel%
)
if /I "%~1"=="stop" (
    shift
    call "%SCRIPT_DIR%EXIT.bat" %*
    exit /b %errorlevel%
)
if not "%~1"=="" (
    echo [ERROR] Unknown command: %~1
    goto :usage
)

:menu
cls
echo [****| HueyOS Windows batch menu |****]
echo.
echo   1. Full local setup
echo   2. Minimal local setup
echo   3. Cleanup local environment
echo   4. Windows Terminal helper
echo   5. Update local environment
echo   6. Build helper
echo   7. Docker helper
echo   8. Docker volume helper
echo   9. Kubernetes helper
echo   10. Start services or app
echo   R. Run the project
echo   T. Run the tests
echo   X. Stop docker or minikube services
echo   Q. Quit
echo.
set /p "CHOICE=Select an option: "
if /I "%CHOICE%"=="1" call "%SCRIPT_DIR%01-FULL.bat" & goto :pause_then_menu
if /I "%CHOICE%"=="2" call "%SCRIPT_DIR%02-MINI.bat" & goto :pause_then_menu
if /I "%CHOICE%"=="3" call "%SCRIPT_DIR%03-CLEANUP.bat" & goto :pause_then_menu
if /I "%CHOICE%"=="4" call "%SCRIPT_DIR%04-TERMINAL.bat" & goto :pause_then_menu
if /I "%CHOICE%"=="5" call "%SCRIPT_DIR%05-UPDATE.bat" & goto :pause_then_menu
if /I "%CHOICE%"=="6" call "%SCRIPT_DIR%06-BUILD.bat" & goto :pause_then_menu
if /I "%CHOICE%"=="7" call "%SCRIPT_DIR%07-CONTAINER.bat" help & goto :pause_then_menu
if /I "%CHOICE%"=="8" call "%SCRIPT_DIR%08-VOLUME.bat" help & goto :pause_then_menu
if /I "%CHOICE%"=="9" call "%SCRIPT_DIR%09-KUBERNETES.bat" help & goto :pause_then_menu
if /I "%CHOICE%"=="10" call "%SCRIPT_DIR%10-START.bat" & goto :pause_then_menu
if /I "%CHOICE%"=="R" call "%SCRIPT_DIR%run.bat" & goto :pause_then_menu
if /I "%CHOICE%"=="T" call "%SCRIPT_DIR%run-tests.bat" & goto :pause_then_menu
if /I "%CHOICE%"=="X" call "%SCRIPT_DIR%EXIT.bat" & goto :pause_then_menu
if /I "%CHOICE%"=="Q" exit /b 0
echo Invalid selection.
goto :pause_then_menu

:pause_then_menu
echo.
pause
goto :menu

:usage
echo Usage: %~nx0 [install^|mini^|cleanup^|terminal^|update^|build^|docker^|volumes^|k8s^|start^|run^|tests^|stop]
echo.
echo Run without arguments to open the interactive Windows batch menu.
exit /b 0
