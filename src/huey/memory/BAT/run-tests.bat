@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "USE_COVERAGE=1"
set "PYTEST_ARGS="

:parse_args
if "%~1"=="" goto :args_done
if /I "%~1"=="help" goto :usage
if /I "%~1"=="--help" goto :usage
if /I "%~1"=="/?" goto :usage
if /I "%~1"=="--no-cov" (
    set "USE_COVERAGE=0"
    shift
    goto :parse_args
)
set "PYTEST_ARGS=%PYTEST_ARGS% %~1"
shift
goto :parse_args

:args_done
call "%SCRIPT_DIR%_common.bat" :resolve_repo_root ROOT_DIR "%SCRIPT_DIR%"
if errorlevel 1 (
    echo [ERROR] Could not locate the repository root from "%SCRIPT_DIR%".
    exit /b 1
)

call "%SCRIPT_DIR%_common.bat" :resolve_python "%ROOT_DIR%" PYTHON_EXE
if errorlevel 1 (
    echo [ERROR] Python was not found. Install Python or create "%ROOT_DIR%\venv" first.
    exit /b 1
)

"%PYTHON_EXE%" -c "import pytest" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pytest is not installed for "%PYTHON_EXE%".
    echo         Run install.bat first to bootstrap the local environment.
    exit /b 1
)

if "%USE_COVERAGE%"=="1" (
    "%PYTHON_EXE%" -c "import pytest_cov" >nul 2>&1
    if errorlevel 1 (
        echo [INFO] pytest-cov is unavailable; running tests without coverage.
        set "USE_COVERAGE=0"
    )
)

call "%SCRIPT_DIR%_common.bat" :timestamp RUN_STAMP
set "LOG_DIR=%ROOT_DIR%\src\huey\memory\LOGS"
set "LOG_FILE=%LOG_DIR%\test_results_%RUN_STAMP%.log"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

pushd "%ROOT_DIR%" >nul
if "%USE_COVERAGE%"=="1" (
    "%PYTHON_EXE%" -m pytest --cov=huey --cov-report=term %PYTEST_ARGS% > "%LOG_FILE%" 2>&1
) else (
    "%PYTHON_EXE%" -m pytest %PYTEST_ARGS% > "%LOG_FILE%" 2>&1
)
set "EXIT_CODE=%errorlevel%"
popd >nul

type "%LOG_FILE%"
echo.
echo Test log: "%LOG_FILE%"
exit /b %EXIT_CODE%

:usage
echo Usage: %~nx0 [pytest args]
echo.
echo Options:
echo   --no-cov   Skip coverage even when pytest-cov is installed.
echo   help       Show this help text.
echo.
echo Any other arguments are forwarded to pytest.
exit /b 0
