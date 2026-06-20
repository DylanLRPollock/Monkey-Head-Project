@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "COMMAND=%~1"
if not defined COMMAND set "COMMAND=tests"

if /I "%COMMAND%"=="help" goto :usage
if /I "%COMMAND%"=="--help" goto :usage
if /I "%COMMAND%"=="/?" goto :usage

if /I "%COMMAND%"=="tests" (
    shift
    call "%SCRIPT_DIR%run-tests.bat" %*
    exit /b %errorlevel%
)

if /I "%COMMAND%"=="docs" (
    shift
    call "%SCRIPT_DIR%make.bat" html %*
    exit /b %errorlevel%
)

if /I "%COMMAND%"=="all" (
    call "%SCRIPT_DIR%run-tests.bat"
    if errorlevel 1 exit /b %errorlevel%
    call "%SCRIPT_DIR%make.bat" html
    exit /b %errorlevel%
)

if /I "%COMMAND%"=="package" goto :package
if /I "%COMMAND%"=="installer" goto :installer

echo [ERROR] Unknown build command: %COMMAND%
goto :usage

:package
call "%SCRIPT_DIR%_common.bat" :resolve_repo_root ROOT_DIR "%SCRIPT_DIR%"
if errorlevel 1 (
    echo [ERROR] Could not locate the repository root from "%SCRIPT_DIR%".
    exit /b 1
)
call "%SCRIPT_DIR%_common.bat" :resolve_python "%ROOT_DIR%" PYTHON_EXE
if errorlevel 1 (
    echo [ERROR] Python was not found.
    exit /b 1
)
"%PYTHON_EXE%" -c "import build" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] The "build" module is not installed in the active Python environment.
    echo         Install it first if you want to create source or wheel packages.
    exit /b 1
)
pushd "%ROOT_DIR%" >nul
"%PYTHON_EXE%" -m build
set "EXIT_CODE=%errorlevel%"
popd >nul
exit /b %EXIT_CODE%

:installer
echo [ERROR] This repository does not currently define a standalone Windows installer packaging pipeline.
exit /b 1

:usage
echo Usage: %~nx0 [tests^|docs^|all^|package^|installer] [extra args]
echo.
echo Commands:
echo   tests      Run the local test suite. Default.
echo   docs       Build the Sphinx HTML documentation.
echo   all        Run tests, then build docs.
echo   package    Build Python source and wheel artifacts when python -m build is available.
echo   installer  Report that no dedicated installer packaging pipeline is defined.
exit /b 0
