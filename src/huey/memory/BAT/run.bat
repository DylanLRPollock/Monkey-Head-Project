@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
call "%SCRIPT_DIR%_common.bat" :resolve_repo_root ROOT_DIR "%SCRIPT_DIR%"
if errorlevel 1 (
    echo [ERROR] Could not locate the repository root from "%SCRIPT_DIR%".
    exit /b 1
)

if /I "%~1"=="help" goto :usage
if /I "%~1"=="--help" goto :usage
if /I "%~1"=="/?" goto :usage

if /I "%~1"=="tests" (
    shift
    call "%SCRIPT_DIR%run-tests.bat" %*
    exit /b %errorlevel%
)
if /I "%~1"=="--tests" (
    shift
    call "%SCRIPT_DIR%run-tests.bat" %*
    exit /b %errorlevel%
)

call "%SCRIPT_DIR%_common.bat" :resolve_python "%ROOT_DIR%" PYTHON_EXE
if errorlevel 1 (
    echo [ERROR] Python was not found. Install Python or create "%ROOT_DIR%\venv" first.
    exit /b 1
)

if not exist "%ROOT_DIR%\run.py" (
    echo [ERROR] Launcher not found: "%ROOT_DIR%\run.py"
    exit /b 1
)

pushd "%ROOT_DIR%" >nul
"%PYTHON_EXE%" "%ROOT_DIR%\run.py" %*
set "EXIT_CODE=%errorlevel%"
popd >nul

exit /b %EXIT_CODE%

:usage
echo Usage: %~nx0 [run.py args]
echo.
echo Helpers:
echo   %~nx0 tests [pytest args]   Run the project's test suite.
echo   %~nx0 help                  Show this help text.
echo.
echo All other arguments are forwarded to "%ROOT_DIR%\run.py".
exit /b 0
