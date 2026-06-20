@echo off
REM Monkey Head Project
REM By: Dylan L.R. Pollock
REM www.dlrp.ca
REM HueyOS: Windows Update script (unified)

REM ==================================================
REM This file is a part of the 'Monkey Head Project'
REM Website:  https://dlrp.ca
REM GitHub:   https://github.com/DylanLRPollock/Monkey-Head-Project
REM License:  GPL-3.0 (https://opensource.org/license/gpl-3-0)
REM Updated:  2026-01-05
REM ==================================================

setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "ERROR_LOG=%SCRIPT_DIR%error_log.txt"

set "INSTALL_DIR="
set "FORCE=0"
set "RECREATE_VENV=0"
set "SYSTEM_UPDATES=0"
set "UPDATE_DOCKER_IMAGES=0"
set "UPDATE_VSCODE_EXTS=0"
set "UPDATE_PS_MODULES=0"

set "PRELOAD_DATA=0"

REM ----------------------------
REM Arg parsing
REM ----------------------------
:parseArgs
if "%~1"=="" goto :argsDone

if /I "%~1"=="--help"            goto :usage
if /I "%~1"=="-h"                goto :usage

if /I "%~1"=="--install-dir"     ( set "INSTALL_DIR=%~2" & shift & shift & goto :parseArgs )
if /I "%~1"=="--force"           ( set "FORCE=1" & shift & goto :parseArgs )
if /I "%~1"=="--recreate-venv"   ( set "RECREATE_VENV=1" & shift & goto :parseArgs )

if /I "%~1"=="--system"          ( set "SYSTEM_UPDATES=1" & shift & goto :parseArgs )
if /I "%~1"=="--docker-images"   ( set "UPDATE_DOCKER_IMAGES=1" & shift & goto :parseArgs )
if /I "%~1"=="--vscode-exts"     ( set "UPDATE_VSCODE_EXTS=1" & shift & goto :parseArgs )
if /I "%~1"=="--ps-modules"      ( set "UPDATE_PS_MODULES=1" & shift & goto :parseArgs )

if /I "%~1"=="--preload-data"    ( set "PRELOAD_DATA=1" & shift & goto :parseArgs )

echo Unknown argument: %~1
goto :usage

:argsDone

REM ----------------------------
REM Resolve install dir (if not provided)
REM ----------------------------
if not defined INSTALL_DIR (
    if exist "%ProgramFiles%\Monkey-Head-Project\.hueyos_install.env" (
        set "INSTALL_DIR=%ProgramFiles%\Monkey-Head-Project"
    ) else if exist "%LOCALAPPDATA%\Monkey-Head-Project\.hueyos_install.env" (
        set "INSTALL_DIR=%LOCALAPPDATA%\Monkey-Head-Project"
    ) else if exist "%ProgramFiles%\Monkey-Head-Project" (
        set "INSTALL_DIR=%ProgramFiles%\Monkey-Head-Project"
    ) else if exist "%LOCALAPPDATA%\Monkey-Head-Project" (
        set "INSTALL_DIR=%LOCALAPPDATA%\Monkey-Head-Project"
    )
)

if not defined INSTALL_DIR (
    echo [ERROR] Could not locate an existing installation.
    echo        Provide --install-dir PATH
    exit /b 1
)

set "META=%INSTALL_DIR%\.hueyos_install.env"
if exist "%META%" (
    call :loadMetadata "%META%"
)

REM ----------------------------
REM Elevation decision
REM - Update may require admin if installed under Program Files or if --system is used.
REM ----------------------------
set "NEEDS_ADMIN=0"
echo "%INSTALL_DIR%" | find /I "%ProgramFiles%" >nul 2>&1
if %errorlevel%==0 set "NEEDS_ADMIN=1"
if "%SYSTEM_UPDATES%"=="1" set "NEEDS_ADMIN=1"

if "%NEEDS_ADMIN%"=="1" call :ensureAdmin

REM ----------------------------
REM Update repo
REM ----------------------------
call :updateRepository

REM ----------------------------
REM Update Python venv + deps
REM ----------------------------
call :updatePythonEnv

REM ----------------------------
REM Optional preload
REM ----------------------------
if "%PRELOAD_DATA%"=="1" (
    echo [INFO] Preloading bundled data (best-effort)...
    "%VENV_PY%" -m huey.os.scripts.preload_data --summary
)

REM ----------------------------
REM Optional system updates (logic derived from 05-UPDATE.bat)
REM ----------------------------
if "%SYSTEM_UPDATES%"=="1" (
    call :ensureChocolatey
    call :refreshEnv

    echo Updating Chocolatey...
    choco upgrade chocolatey -y
    call :checkError "Chocolatey Update"

    echo Updating all installed Chocolatey packages...
    choco upgrade all -y
    call :checkError "Chocolatey Packages Update"
)

if "%UPDATE_VSCODE_EXTS%"=="1" (
    call :updateVSCodeExtensions
)

if "%UPDATE_PS_MODULES%"=="1" (
    call :updatePSModules
)

if "%UPDATE_DOCKER_IMAGES%"=="1" (
    call :updateDockerImages
)

REM ----------------------------
REM Update metadata timestamp
REM ----------------------------
call :writeUpdateTimestamp

echo.
echo [****| Update complete! |****]
pause
exit /b 0

REM ==================================================
REM Functions
REM ==================================================

:usage
echo.
echo Usage: %~nx0 [options]
echo.
echo   --install-dir PATH         Target install directory (auto-detected if omitted)
echo   --force                    Discard local git changes (git reset/clean)
echo   --recreate-venv            Delete and rebuild the venv before reinstalling deps
echo.
echo System updates (optional):
echo   --system                   choco upgrade chocolatey + all packages
echo   --docker-images            docker pull all locally tagged images
echo   --vscode-exts              update VSCode extensions (best-effort)
echo   --ps-modules               update PowerShell modules (best-effort)
echo.
echo Other:
echo   --preload-data             run data preload (best-effort)
echo.
exit /b 2

:logError
echo %date% %time% - Error: %~1 (exit=%errorlevel%)>> "%ERROR_LOG%"
goto :eof

:checkError
if %errorlevel% neq 0 (
    echo [ERROR] %~1 failed (exit=%errorlevel%)
    call :logError "%~1"
    exit /b %errorlevel%
)
goto :eof

:ensureAdmin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrative privileges...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -ArgumentList '%*' -Verb RunAs"
    exit /b 0
)
goto :eof

:ensureChocolatey
where choco >nul 2>&1
if %errorlevel%==0 goto :eof

echo Chocolatey not found. Installing Chocolatey...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Set-ExecutionPolicy Bypass -Scope Process -Force; ^
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; ^
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
call :checkError "Chocolatey Installation"
goto :eof

:refreshEnv
if exist "%ProgramData%\chocolatey\bin\refreshenv.cmd" (
    call "%ProgramData%\chocolatey\bin\refreshenv.cmd" >nul
)
goto :eof

:loadMetadata
REM Loads simple KEY=VALUE lines into environment variables
for /f "usebackq tokens=1,* delims==" %%A in ("%~1") do (
    set "%%A=%%B"
)
goto :eof

:updateRepository
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] git not found. Cannot update repository.
    exit /b 1
)

if not exist "%INSTALL_DIR%\.git" (
    echo [WARN] No .git directory found. This install may not be a git clone.
    echo        Consider reinstalling (install script) if you need to update code.
    goto :eof
)

echo Updating repository in "%INSTALL_DIR%"...

if "%FORCE%"=="0" (
    for /f "delims=" %%S in ('git -C "%INSTALL_DIR%" status --porcelain') do (
        echo [ERROR] Local changes detected. Re-run with --force to discard changes.
        exit /b 1
    )
) else (
    echo Discarding local changes (force)...
    git -C "%INSTALL_DIR%" reset --hard
    call :checkError "Git Reset"
    git -C "%INSTALL_DIR%" clean -fd
    call :checkError "Git Clean"
)

git -C "%INSTALL_DIR%" pull --recurse-submodules
call :checkError "Git Pull"

git -C "%INSTALL_DIR%" submodule update --init --recursive
call :checkError "Git Submodule Update"

goto :eof

:updatePythonEnv
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] python not found. Cannot update Python environment.
    exit /b 1
)

cd /d "%INSTALL_DIR%"

if "%RECREATE_VENV%"=="1" (
    if exist "%INSTALL_DIR%\venv" (
        echo Removing existing venv...
        rmdir /S /Q "%INSTALL_DIR%\venv"
        call :checkError "Remove venv"
    )
)

if not exist "%INSTALL_DIR%\venv" (
    echo Creating venv...
    python -m venv "%INSTALL_DIR%\venv"
    call :checkError "Create venv"
)

set "VENV_PY=%INSTALL_DIR%\venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo [ERROR] venv python not found: "%VENV_PY%"
    exit /b 1
)

echo Upgrading pip...
"%VENV_PY%" -m pip install --upgrade pip
call :checkError "Pip Upgrade"

if exist "%INSTALL_DIR%\requirements.txt" (
    echo Installing requirements...
    "%VENV_PY%" -m pip install -r "%INSTALL_DIR%\requirements.txt"
    call :checkError "Install requirements"
)

if exist "%INSTALL_DIR%\vendor\pygpt\pygpt-mhp" (
    echo Installing pygpt-MHP editable...
    "%VENV_PY%" -m pip install -e "%INSTALL_DIR%\vendor\pygpt\pygpt-mhp"
    call :checkError "Install pygpt-MHP"
)

if exist "%INSTALL_DIR%\sync_pygpt_structure.py" (
    "%VENV_PY%" "%INSTALL_DIR%\sync_pygpt_structure.py"
    call :checkError "Sync structure"
)

if exist "%INSTALL_DIR%\scripts\check_inter_program_connectivity.py" (
    "%VENV_PY%" "%INSTALL_DIR%\scripts\check_inter_program_connectivity.py"
    call :checkError "Connectivity check"
)

goto :eof

:updateVSCodeExtensions
where code >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] VS Code CLI (code) not found; skipping extension update.
    goto :eof
)

echo Updating VSCode extensions (best-effort)...
for /f %%i in ('code --list-extensions') do (
    code --install-extension %%i >nul 2>&1
)
goto :eof

:updatePSModules
echo Updating PowerShell modules (best-effort)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-InstalledModule ^| ForEach-Object { Update-Module -Name $_.Name -Force }" >nul 2>&1
goto :eof

:updateDockerImages
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] docker not found; skipping image update.
    goto :eof
)

echo Updating Docker images (best-effort)...
for /f "delims=" %%i in ('docker images --format "{{.Repository}}:{{.Tag}}" ^| findstr /v "<none>"') do (
    docker pull %%i >nul 2>&1
)
goto :eof

:writeUpdateTimestamp
set "META=%INSTALL_DIR%\.hueyos_install.env"
if not exist "%META%" goto :eof
echo.>> "%META%"
>> "%META%" echo UPDATED_AT=%date% %time%
goto :eof
