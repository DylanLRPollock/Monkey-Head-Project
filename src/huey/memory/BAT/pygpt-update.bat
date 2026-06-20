@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
call "%SCRIPT_DIR%_common.bat" :resolve_repo_root ROOT_DIR "%SCRIPT_DIR%"
if errorlevel 1 (
    echo [ERROR] Could not locate the repository root from "%SCRIPT_DIR%".
    exit /b 1
)

set "VENV_PYTHON=%ROOT_DIR%\venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
    echo [ERROR] Local virtual environment not found. Run install.bat first.
    exit /b 1
)

pushd "%ROOT_DIR%" >nul
if exist "%ROOT_DIR%\vendor\pygpt\pygpt-mhp" (
    "%VENV_PYTHON%" -m pip install -e "%ROOT_DIR%\vendor\pygpt\pygpt-mhp"
    if errorlevel 1 (
        popd >nul
        exit /b 1
    )
    if exist "%ROOT_DIR%\src\huey\memory\PY\sync_pygpt_structure.py" (
        "%VENV_PYTHON%" "%ROOT_DIR%\src\huey\memory\PY\sync_pygpt_structure.py"
        if errorlevel 1 (
            popd >nul
            exit /b 1
        )
    )
) else (
    "%VENV_PYTHON%" -m pip install --upgrade pygpt-net
    if errorlevel 1 (
        popd >nul
        exit /b 1
    )
)
popd >nul

exit /b 0
