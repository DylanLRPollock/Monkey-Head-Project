@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "COMMAND=%~1"
if not defined COMMAND set "COMMAND=help"

if /I "%COMMAND%"=="help" goto :usage
if /I "%COMMAND%"=="--help" goto :usage
if /I "%COMMAND%"=="/?" goto :usage

where kubectl >nul 2>&1
if errorlevel 1 (
    echo [ERROR] kubectl is not available.
    exit /b 1
)

call "%SCRIPT_DIR%_common.bat" :resolve_repo_root ROOT_DIR "%SCRIPT_DIR%"
if errorlevel 1 (
    echo [ERROR] Could not locate the repository root from "%SCRIPT_DIR%".
    exit /b 1
)
set "MANIFEST_DIR=%ROOT_DIR%\k8s"

if /I "%COMMAND%"=="context" (
    kubectl config current-context
    exit /b %errorlevel%
)

if /I "%COMMAND%"=="status" (
    set "NAMESPACE=%~2"
    if not defined NAMESPACE set "NAMESPACE=default"
    kubectl get pods -n "%NAMESPACE%"
    exit /b %errorlevel%
)

if /I "%COMMAND%"=="pods" (
    set "NAMESPACE=%~2"
    if not defined NAMESPACE set "NAMESPACE=default"
    kubectl get pods -n "%NAMESPACE%"
    exit /b %errorlevel%
)

if /I "%COMMAND%"=="apply" (
    set "NAMESPACE=%~2"
    if not defined NAMESPACE set "NAMESPACE=default"
    if not exist "%MANIFEST_DIR%" (
        echo [ERROR] Manifest directory not found: "%MANIFEST_DIR%"
        exit /b 1
    )
    kubectl apply -n "%NAMESPACE%" -f "%MANIFEST_DIR%"
    exit /b %errorlevel%
)

if /I "%COMMAND%"=="delete" (
    set "NAMESPACE=%~2"
    set "ALLOW_DEFAULT=0"
    set "CONFIRMED=0"
    if not defined NAMESPACE (
        echo [ERROR] delete requires a namespace argument.
        exit /b 2
    )
    if /I "%~3"=="--allow-default" set "ALLOW_DEFAULT=1"
    if /I "%~4"=="--allow-default" set "ALLOW_DEFAULT=1"
    if /I "%~3"=="--yes" set "CONFIRMED=1"
    if /I "%~4"=="--yes" set "CONFIRMED=1"
    if "%CONFIRMED%"=="0" (
        echo [ERROR] delete requires --yes for confirmation.
        exit /b 2
    )
    if /I "%NAMESPACE%"=="default" if "%ALLOW_DEFAULT%"=="0" (
        echo [ERROR] Refusing to delete resources from the default namespace without --allow-default.
        exit /b 2
    )
    if not exist "%MANIFEST_DIR%" (
        echo [ERROR] Manifest directory not found: "%MANIFEST_DIR%"
        exit /b 1
    )
    kubectl delete -n "%NAMESPACE%" -f "%MANIFEST_DIR%"
    exit /b %errorlevel%
)

echo [ERROR] Unknown Kubernetes command: %COMMAND%
goto :usage

:usage
echo Usage: %~nx0 [context^|status^|pods^|apply^|delete] [namespace] [flags]
echo.
echo Commands:
echo   context
echo   status [namespace]
echo   pods [namespace]
echo   apply [namespace]
echo   delete NAMESPACE --yes [--allow-default]
echo.
echo The manifest directory is expected at "<repo>\k8s".
exit /b 0
