@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
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

pushd "%ROOT_DIR%" >nul
set "PYTHONPATH=%ROOT_DIR%\src;%PYTHONPATH%"
"%PYTHON_EXE%" -c "from huey.pygpt_custom_cli import CustomPyGPT; CustomPyGPT().run_cli()"
set "EXIT_CODE=%errorlevel%"
popd >nul

exit /b %EXIT_CODE%
