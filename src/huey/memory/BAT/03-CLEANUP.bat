@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "DRY_RUN=1"
set "REMOVE_VENV=1"
set "REMOVE_PYTEST_CACHE=1"
set "REMOVE_PYTHON_CACHE=1"
set "REMOVE_RUFF_CACHE=1"
set "REMOVE_LOGS=0"
set "PURGE_PIP_CACHE=0"
set "PURGE_NPM_CACHE=0"
set "DOCKER_PRUNE=0"

:parse_args
if "%~1"=="" goto :args_done
if /I "%~1"=="help" goto :usage
if /I "%~1"=="--help" goto :usage
if /I "%~1"=="/?" goto :usage
if /I "%~1"=="--yes" (
    set "DRY_RUN=0"
    shift
    goto :parse_args
)
if /I "%~1"=="--dry-run" (
    set "DRY_RUN=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--logs" (
    set "REMOVE_LOGS=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--pip-cache" (
    set "PURGE_PIP_CACHE=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--npm-cache" (
    set "PURGE_NPM_CACHE=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--docker-prune" (
    set "DOCKER_PRUNE=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--all" (
    set "REMOVE_LOGS=1"
    set "PURGE_PIP_CACHE=1"
    set "PURGE_NPM_CACHE=1"
    shift
    goto :parse_args
)
echo [ERROR] Unknown argument: %~1
goto :usage

:args_done
call "%SCRIPT_DIR%_common.bat" :resolve_repo_root ROOT_DIR "%SCRIPT_DIR%"
if errorlevel 1 (
    echo [ERROR] Could not locate the repository root from "%SCRIPT_DIR%".
    exit /b 1
)

set "VENV_DIR=%ROOT_DIR%\venv"
set "PYTEST_CACHE=%ROOT_DIR%\.pytest_cache"
set "RUFF_CACHE=%ROOT_DIR%\.ruff_cache"
set "LOG_DIR=%ROOT_DIR%\src\huey\memory\LOGS"
set "EXIT_CODE=0"

if "%DRY_RUN%"=="1" (
    echo [dry-run] Repository cleanup preview for "%ROOT_DIR%"
)

if "%REMOVE_VENV%"=="1" if exist "%VENV_DIR%" (
    if "%DRY_RUN%"=="1" (
        echo [dry-run] Remove "%VENV_DIR%"
    ) else (
        rmdir /S /Q "%VENV_DIR%"
        if errorlevel 1 set "EXIT_CODE=1"
    )
)

if "%REMOVE_PYTEST_CACHE%"=="1" if exist "%PYTEST_CACHE%" (
    if "%DRY_RUN%"=="1" (
        echo [dry-run] Remove "%PYTEST_CACHE%"
    ) else (
        rmdir /S /Q "%PYTEST_CACHE%"
        if errorlevel 1 set "EXIT_CODE=1"
    )
)

if "%REMOVE_RUFF_CACHE%"=="1" if exist "%RUFF_CACHE%" (
    if "%DRY_RUN%"=="1" (
        echo [dry-run] Remove "%RUFF_CACHE%"
    ) else (
        rmdir /S /Q "%RUFF_CACHE%"
        if errorlevel 1 set "EXIT_CODE=1"
    )
)

if "%REMOVE_PYTHON_CACHE%"=="1" (
    if "%DRY_RUN%"=="1" (
        echo [dry-run] Remove __pycache__ directories and *.pyc files under "%ROOT_DIR%"
    ) else (
        for /d /r "%ROOT_DIR%" %%D in (__pycache__) do if exist "%%~fD" rd /S /Q "%%~fD"
        del /S /F /Q "%ROOT_DIR%\*.pyc" >nul 2>&1
    )
)

if "%REMOVE_LOGS%"=="1" if exist "%LOG_DIR%" (
    if "%DRY_RUN%"=="1" (
        echo [dry-run] Remove "%LOG_DIR%"
    ) else (
        rmdir /S /Q "%LOG_DIR%"
        if errorlevel 1 set "EXIT_CODE=1"
    )
)

if "%PURGE_PIP_CACHE%"=="1" (
    call "%SCRIPT_DIR%_common.bat" :resolve_python "%ROOT_DIR%" PYTHON_EXE
    if errorlevel 1 (
        echo [WARN] Python not found; skipping pip cache purge.
    ) else if "%DRY_RUN%"=="1" (
        echo [dry-run] Run "%PYTHON_EXE% -m pip cache purge"
    ) else (
        "%PYTHON_EXE%" -m pip cache purge
        if errorlevel 1 set "EXIT_CODE=1"
    )
)

if "%PURGE_NPM_CACHE%"=="1" (
    where npm >nul 2>&1
    if errorlevel 1 (
        echo [WARN] npm not found; skipping npm cache purge.
    ) else if "%DRY_RUN%"=="1" (
        echo [dry-run] Run "npm cache clean --force"
    ) else (
        npm cache clean --force
        if errorlevel 1 set "EXIT_CODE=1"
    )
)

if "%DOCKER_PRUNE%"=="1" (
    where docker >nul 2>&1
    if errorlevel 1 (
        echo [WARN] docker not found; skipping docker cleanup.
    ) else if "%DRY_RUN%"=="1" (
        echo [dry-run] Run "docker system prune -a --volumes"
    ) else (
        docker system prune -a -f --volumes
        if errorlevel 1 set "EXIT_CODE=1"
    )
)

if "%DRY_RUN%"=="1" (
    echo.
    echo Re-run with --yes to apply these cleanup actions.
)

exit /b %EXIT_CODE%

:usage
echo Usage: %~nx0 [options]
echo.
echo Default behavior: preview cleanup of the local venv and Python caches.
echo.
echo Options:
echo   --yes            Apply the selected cleanup actions.
echo   --dry-run        Show the actions without applying them. Default.
echo   --logs           Remove src\huey\memory\LOGS.
echo   --pip-cache      Purge the active Python pip cache.
echo   --npm-cache      Purge the global npm cache.
echo   --docker-prune   Run "docker system prune -a --volumes".
echo   --all            Include logs plus pip/npm cache purges.
exit /b 0
