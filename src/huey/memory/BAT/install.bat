@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "PROFILE=full"
set "UPGRADE_PIP=1"
set "INSTALL_EDITABLE="
set "RUN_SYNC=1"
set "RUN_CONNECTIVITY=1"
set "SHOW_LICENSE_GUI=0"
set "RECREATE_VENV=0"

:parse_args
if "%~1"=="" goto :args_done
if /I "%~1"=="help" goto :usage
if /I "%~1"=="--help" goto :usage
if /I "%~1"=="/?" goto :usage
if /I "%~1"=="--profile" (
    if "%~2"=="" (
        echo [ERROR] --profile requires a value: full or mini.
        exit /b 2
    )
    set "PROFILE=%~2"
    shift
    shift
    goto :parse_args
)
if /I "%~1"=="--skip-pip-upgrade" (
    set "UPGRADE_PIP=0"
    shift
    goto :parse_args
)
if /I "%~1"=="--skip-sync" (
    set "RUN_SYNC=0"
    shift
    goto :parse_args
)
if /I "%~1"=="--skip-connectivity" (
    set "RUN_CONNECTIVITY=0"
    shift
    goto :parse_args
)
if /I "%~1"=="--with-pygpt" (
    set "INSTALL_EDITABLE=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--without-pygpt" (
    set "INSTALL_EDITABLE=0"
    shift
    goto :parse_args
)
if /I "%~1"=="--license-gui" (
    set "SHOW_LICENSE_GUI=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--skip-license-gui" (
    set "SHOW_LICENSE_GUI=0"
    shift
    goto :parse_args
)
if /I "%~1"=="--recreate-venv" (
    set "RECREATE_VENV=1"
    shift
    goto :parse_args
)
echo [ERROR] Unknown argument: %~1
goto :usage

:args_done
if /I not "%PROFILE%"=="full" if /I not "%PROFILE%"=="mini" (
    echo [ERROR] Invalid profile "%PROFILE%". Use "full" or "mini".
    exit /b 2
)

if not defined INSTALL_EDITABLE (
    if /I "%PROFILE%"=="mini" (
        set "INSTALL_EDITABLE=0"
    ) else (
        set "INSTALL_EDITABLE=1"
    )
)

call "%SCRIPT_DIR%_common.bat" :resolve_repo_root ROOT_DIR "%SCRIPT_DIR%"
if errorlevel 1 (
    echo [ERROR] Could not locate the repository root from "%SCRIPT_DIR%".
    exit /b 1
)

if not exist "%ROOT_DIR%\requirements.txt" (
    echo [ERROR] requirements.txt not found at "%ROOT_DIR%\requirements.txt".
    exit /b 1
)

call "%SCRIPT_DIR%_common.bat" :resolve_python "%ROOT_DIR%" BOOTSTRAP_PYTHON
if errorlevel 1 (
    echo [ERROR] Python was not found. Install Python 3.10+ and try again.
    exit /b 1
)

set "VENV_DIR=%ROOT_DIR%\venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

if "%RECREATE_VENV%"=="1" if exist "%VENV_DIR%" (
    echo Removing existing virtual environment...
    rmdir /S /Q "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to remove "%VENV_DIR%".
        exit /b 1
    )
)

if not exist "%VENV_PYTHON%" (
    echo Creating virtual environment at "%VENV_DIR%"...
    pushd "%ROOT_DIR%" >nul
    "%BOOTSTRAP_PYTHON%" -m venv "%VENV_DIR%"
    set "EXIT_CODE=%errorlevel%"
    popd >nul
    if not "%EXIT_CODE%"=="0" exit /b %EXIT_CODE%
)

if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual environment bootstrap failed: "%VENV_PYTHON%" was not created.
    exit /b 1
)

if not exist "%ROOT_DIR%\src\huey\memory\LOGS" mkdir "%ROOT_DIR%\src\huey\memory\LOGS" >nul 2>&1
if not exist "%ROOT_DIR%\src\huey\memory\RAW" mkdir "%ROOT_DIR%\src\huey\memory\RAW" >nul 2>&1

pushd "%ROOT_DIR%" >nul
if "%UPGRADE_PIP%"=="1" (
    "%VENV_PYTHON%" -m pip install --upgrade pip
    if errorlevel 1 (
        popd >nul
        exit /b 1
    )
)

echo Installing repository requirements for the "%PROFILE%" profile...
"%VENV_PYTHON%" -m pip install -r "%ROOT_DIR%\requirements.txt"
if errorlevel 1 (
    popd >nul
    exit /b 1
)

if "%INSTALL_EDITABLE%"=="1" (
    if exist "%ROOT_DIR%\vendor\pygpt\pygpt-mhp" (
        echo Installing vendored pygpt-mhp in editable mode...
        "%VENV_PYTHON%" -m pip install -e "%ROOT_DIR%\vendor\pygpt\pygpt-mhp"
        if errorlevel 1 (
            popd >nul
            exit /b 1
        )
    ) else (
        echo [INFO] Vendored PyGPT package not found; skipping editable install.
    )
)

if "%RUN_SYNC%"=="1" if exist "%ROOT_DIR%\src\huey\memory\PY\sync_pygpt_structure.py" (
    echo Synchronizing vendored PyGPT structure...
    "%VENV_PYTHON%" "%ROOT_DIR%\src\huey\memory\PY\sync_pygpt_structure.py"
    if errorlevel 1 (
        popd >nul
        exit /b 1
    )
)

if "%RUN_CONNECTIVITY%"=="1" if exist "%ROOT_DIR%\scripts\check_inter_program_connectivity.py" (
    echo Running inter-program connectivity checks...
    "%VENV_PYTHON%" "%ROOT_DIR%\scripts\check_inter_program_connectivity.py"
    if errorlevel 1 (
        popd >nul
        exit /b 1
    )
)

if "%SHOW_LICENSE_GUI%"=="1" (
    echo Attempting to display the license agreement...
    set "PYTHONPATH=%ROOT_DIR%\src;%PYTHONPATH%"
    "%VENV_PYTHON%" -c "from huey.os.license_gui import show_license_gui; show_license_gui()"
    if errorlevel 1 echo [WARN] License GUI could not be displayed in this environment.
)
popd >nul

echo.
echo [****| Local environment setup complete. |****]
echo   Repository root: "%ROOT_DIR%"
echo   Virtual env:     "%VENV_DIR%"
exit /b 0

:usage
echo Usage: %~nx0 [options]
echo.
echo Options:
echo   --profile full^|mini      Choose the local setup profile. Default: full.
echo   --recreate-venv           Rebuild the repository virtual environment.
echo   --skip-pip-upgrade        Leave the current pip version unchanged.
echo   --skip-sync               Skip sync_pygpt_structure.py.
echo   --skip-connectivity       Skip scripts\check_inter_program_connectivity.py.
echo   --with-pygpt              Force the editable vendored PyGPT install.
echo   --without-pygpt           Skip the editable vendored PyGPT install.
echo   --license-gui             Attempt to show the legacy license GUI.
echo   --skip-license-gui        Skip the license GUI.
exit /b 0
