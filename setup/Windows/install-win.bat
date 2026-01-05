@echo off
REM Monkey Head Project
REM By: Dylan L.R. Pollock
REM www.dlrp.ca
REM HueyOS: Windows Install script (unified)

REM ==================================================
REM This file is a part of the 'Monkey Head Project'
REM Website:  https://dlrp.ca
REM GitHub:   https://github.com/DylanLRPollock/Monkey-Head-Project
REM License:  GPL-3.0 (https://opensource.org/license/gpl-3-0)
REM Updated:  2026-01-05
REM ==================================================

setlocal EnableExtensions EnableDelayedExpansion

REM ----------------------------
REM Defaults
REM ----------------------------
set "REPO_URL=https://github.com/DylanLRPollock/Monkey-Head-Project.git"
set "PROFILE=full"
set "SKIP_DEPS=0"
set "WITH_DOCKER=0"
set "WITH_K8S=0"
set "WITH_TOOLS=0"
set "FORCE_OVERWRITE=0"
set "NON_INTERACTIVE=0"
set "ACCEPT_LICENSE=0"
set "SKIP_LICENSE_GUI=0"
set "PRELOAD_DATA=0"
set "USER_INSTALL=0"

set "SCRIPT_DIR=%~dp0"
set "ERROR_LOG=%SCRIPT_DIR%error_log.txt"

REM Install defaults (resolved later after elevation decision)
set "INSTALL_DIR="
set "MEMORY_PATH="

REM Temp file to record choco packages installed by this run
set "DEPS_TMP=%TEMP%\hueyos_choco_deps_%RANDOM%%RANDOM%.txt"
if exist "%DEPS_TMP%" del /q "%DEPS_TMP%" >nul 2>&1

REM ----------------------------
REM Arg parsing
REM ----------------------------
:parseArgs
if "%~1"=="" goto :argsDone

if /I "%~1"=="--help"              goto :usage
if /I "%~1"=="-h"                  goto :usage

if /I "%~1"=="--profile"           ( set "PROFILE=%~2" & shift & shift & goto :parseArgs )
if /I "%~1"=="--install-dir"       ( set "INSTALL_DIR=%~2" & shift & shift & goto :parseArgs )
if /I "%~1"=="--memory-path"       ( set "MEMORY_PATH=%~2" & shift & shift & goto :parseArgs )

if /I "%~1"=="--skip-deps"         ( set "SKIP_DEPS=1" & shift & goto :parseArgs )
if /I "%~1"=="--with-docker"       ( set "WITH_DOCKER=1" & shift & goto :parseArgs )
if /I "%~1"=="--with-k8s"          ( set "WITH_K8S=1" & shift & goto :parseArgs )
if /I "%~1"=="--with-tools"        ( set "WITH_TOOLS=1" & shift & goto :parseArgs )

if /I "%~1"=="--force"             ( set "FORCE_OVERWRITE=1" & shift & goto :parseArgs )

if /I "%~1"=="--non-interactive"   ( set "NON_INTERACTIVE=1" & shift & goto :parseArgs )
if /I "%~1"=="--accept-license"    ( set "ACCEPT_LICENSE=1" & shift & goto :parseArgs )
if /I "%~1"=="--skip-license-gui"  ( set "SKIP_LICENSE_GUI=1" & shift & goto :parseArgs )

if /I "%~1"=="--preload-data"      ( set "PRELOAD_DATA=1" & shift & goto :parseArgs )
if /I "%~1"=="--user"              ( set "USER_INSTALL=1" & shift & goto :parseArgs )

echo Unknown argument: %~1
goto :usage

:argsDone

REM Normalize profile
if /I "%PROFILE%"=="mini" (
    REM ok
) else if /I "%PROFILE%"=="full" (
    REM ok
) else (
    echo Invalid --profile value: "%PROFILE%" (use "full" or "mini")
    exit /b 2
)

REM ----------------------------
REM Decide defaults
REM ----------------------------
if not defined INSTALL_DIR (
    if "%USER_INSTALL%"=="1" (
        set "INSTALL_DIR=%LOCALAPPDATA%\Monkey-Head-Project"
    ) else (
        set "INSTALL_DIR=%ProgramFiles%\Monkey-Head-Project"
    )
)

if not defined MEMORY_PATH (
    set "MEMORY_PATH=%INSTALL_DIR%\memory"
)

REM Dependency install implies admin (Chocolatey is machine-scoped).
set "NEEDS_ADMIN=0"
if "%SKIP_DEPS%"=="0" set "NEEDS_ADMIN=1"
echo "%INSTALL_DIR%" | find /I "%ProgramFiles%" >nul 2>&1
if %errorlevel%==0 set "NEEDS_ADMIN=1"

REM If user requested --user but also wants deps, warn and elevate anyway
if "%USER_INSTALL%"=="1" if "%SKIP_DEPS%"=="0" set "NEEDS_ADMIN=1"

if "%NEEDS_ADMIN%"=="1" call :ensureAdmin

REM ----------------------------
REM Preflight
REM ----------------------------
call :systemCheck

REM ----------------------------
REM Dependencies (Chocolatey)
REM ----------------------------
if "%SKIP_DEPS%"=="0" (
    call :ensureChocolatey
    call :refreshEnv

    call :ensureChocoPackage git "Git"
    call :ensureChocoPackage python "Python"

    if /I "%PROFILE%"=="full" (
        call :ensureChocoPackage nodejs "Node.js"
        call :ensureChocoPackage vscode "VS Code"
        set "WITH_DOCKER=1"
    )

    if "%WITH_DOCKER%"=="1" (
        call :ensureChocoPackage docker-desktop "Docker Desktop"
    )

    if "%WITH_K8S%"=="1" (
        call :ensureChocoPackage kubernetes-cli "kubectl"
        call :ensureChocoPackage minikube "Minikube"
    )

    if "%WITH_TOOLS%"=="1" (
        call :ensureChocoPackage 7zip "7-Zip"
        call :ensureChocoPackage curl "curl"
        call :ensureChocoPackage wget "wget"
    )

    call :refreshEnv
) else (
    echo [INFO] Skipping dependency installation (--skip-deps)
)

REM ----------------------------
REM Clone / install files
REM Logic from 01-FULL.bat: cloneRepository (but safer: refuse unless --force)
REM ----------------------------
call :cloneRepository

REM ----------------------------
REM Memory dirs
REM Logic from 01-FULL.bat: prepareMemoryDirs
REM ----------------------------
call :prepareMemoryDirs

REM ----------------------------
REM Python env
REM Logic from 01-FULL.bat: setupPythonEnv + sync_pygpt_structure.py + connectivity check
REM ----------------------------
call :setupPythonEnv

REM ----------------------------
REM License GUI (best-effort)
REM Logic from 01-FULL.bat: showLicenseGui
REM ----------------------------
call :showLicenseGui

REM ----------------------------
REM Preload data (optional; logic parallels install.sh preload_data)
REM ----------------------------
if "%PRELOAD_DATA%"=="1" (
    echo [INFO] Preloading bundled data (best-effort)...
    "%VENV_PY%" -m hueyos.scripts.preload_data --summary
    REM do not fail install if preload fails
)

REM ----------------------------
REM Write install metadata
REM ----------------------------
call :writeMetadata

echo.
echo ***********************************************
echo   Thank you for supporting the Monkey Head Project!
echo   We hope you enjoy using it.
echo ***********************************************
echo.
echo [****| Install complete! |****]
pause
exit /b 0

REM ==================================================
REM Functions
REM ==================================================

:usage
echo.
echo Usage: %~nx0 [options]
echo.
echo Core options:
echo   --profile full^|mini         Install profile (default: full)
echo   --install-dir PATH           Install destination (default: Program Files unless --user)
echo   --memory-path PATH           Memory directory (default: ^<install^>\memory)
echo   --force                      Overwrite existing install dir
echo.
echo Dependency options:
echo   --skip-deps                  Do not install dependencies (git/python/etc.)
echo   --with-docker                Install Docker Desktop (full profile enables by default)
echo   --with-k8s                   Install kubectl + minikube
echo   --with-tools                 Install a small set of tools (7zip/curl/wget)
echo.
echo Runtime / UI:
echo   --non-interactive            Skip any interactive UI
echo   --accept-license             Skip license UI (explicit acceptance)
echo   --skip-license-gui           Do not attempt to show license GUI
echo   --preload-data               Run data preload step (best-effort)
echo.
echo Scope:
echo   --user                       Default install dir to %%LOCALAPPDATA%% (still elevates if deps install)
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

:systemCheck
echo Performing system checks...
REM Windows 10/11 check (ver shows 10.0.* for both)
ver | find "10.0." >nul
if %errorlevel% neq 0 (
    echo [ERROR] Windows 10/11 required.
    exit /b 1
)

REM Internet check
ping -n 1 github.com >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No internet connectivity detected (cannot reach github.com).
    exit /b 1
)

goto :eof

:ensureChocolatey
where choco >nul 2>&1
if %errorlevel%==0 (
    echo Chocolatey is already installed.
    goto :eof
)

echo Installing Chocolatey...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Set-ExecutionPolicy Bypass -Scope Process -Force; ^
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; ^
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
call :checkError "Chocolatey Installation"
goto :eof

:refreshEnv
REM Best-effort PATH refresh after choco installs
if exist "%ProgramData%\chocolatey\bin\refreshenv.cmd" (
    call "%ProgramData%\chocolatey\bin\refreshenv.cmd" >nul
)
goto :eof

:ensureChocoPackage
set "PKG=%~1"
set "NAME=%~2"

REM Check installed (parse output)
for /f "delims=" %%L in ('choco list --local-only --exact "%PKG%" 2^>nul') do (
    echo %%L | findstr /I /B "%PKG% " >nul
    if !errorlevel!==0 (
        echo %NAME% already installed.
        goto :eof
    )
)

echo Installing %NAME%...
choco install -y "%PKG%"
call :checkError "%NAME% Installation"

REM Record that we installed it (used for optional uninstall purge)
echo %PKG%>> "%DEPS_TMP%"
goto :eof

:cloneRepository
echo Installing to: "%INSTALL_DIR%"

if exist "%INSTALL_DIR%" (
    dir /a /b "%INSTALL_DIR%" >nul 2>&1
    if %errorlevel%==0 (
        REM directory exists; check if non-empty
        for /f %%A in ('dir /a /b "%INSTALL_DIR%" 2^>nul ^| find /c /v ""') do set "COUNT=%%A"
        if not "%COUNT%"=="0" (
            if "%FORCE_OVERWRITE%"=="1" (
                echo Removing existing install directory (force)...
                rmdir /S /Q "%INSTALL_DIR%"
                call :checkError "Removing Existing Install Directory"
            ) else (
                echo [ERROR] Install directory already exists and is not empty: "%INSTALL_DIR%"
                echo         Re-run with --force to overwrite.
                exit /b 1
            )
        )
    )
)

REM Ensure parent dir exists
for %%P in ("%INSTALL_DIR%") do set "INSTALL_PARENT=%%~dpP"
if not exist "!INSTALL_PARENT!" mkdir "!INSTALL_PARENT!" >nul 2>&1

REM Clone
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] git not found. Install git or rerun without --skip-deps.
    exit /b 1
)

echo Cloning repository...
git clone --recurse-submodules "%REPO_URL%" "%INSTALL_DIR%"
call :checkError "Git Clone"

git -C "%INSTALL_DIR%" submodule update --init --recursive
call :checkError "Git Submodule Update"

REM If installed under Program Files, grant current user full control to avoid venv/pip permission issues
echo "%INSTALL_DIR%" | find /I "%ProgramFiles%" >nul 2>&1
if %errorlevel%==0 (
    echo Granting current user permissions to "%INSTALL_DIR%"...
    icacls "%INSTALL_DIR%" /grant "%USERDOMAIN%\%USERNAME%:(OI)(CI)F" /T >nul 2>&1
)

goto :eof

:prepareMemoryDirs
echo Preparing memory directories at "%MEMORY_PATH%"...
if not exist "%MEMORY_PATH%" mkdir "%MEMORY_PATH%"
if not exist "%MEMORY_PATH%\LOGS" mkdir "%MEMORY_PATH%\LOGS"
if not exist "%MEMORY_PATH%\RAW" mkdir "%MEMORY_PATH%\RAW"
goto :eof

:setupPythonEnv
echo Setting up Python environment...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] python not found. Install Python 3.10+ or rerun without --skip-deps.
    exit /b 1
)

REM Require Python 3.10+
python -c "import sys; raise SystemExit(0 if (sys.version_info.major>3 or (sys.version_info.major==3 and sys.version_info.minor>=10)) else 1)"
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.10+ required.
    exit /b 1
)

cd /d "%INSTALL_DIR%"

if not exist "%INSTALL_DIR%\venv" (
    python -m venv "%INSTALL_DIR%\venv"
    call :checkError "Python Virtual Environment Setup"
)

set "VENV_PY=%INSTALL_DIR%\venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo [ERROR] venv python not found: "%VENV_PY%"
    exit /b 1
)

"%VENV_PY%" -m pip install --upgrade pip
call :checkError "Pip Upgrade"

if exist "%INSTALL_DIR%\requirements.txt" (
    "%VENV_PY%" -m pip install -r "%INSTALL_DIR%\requirements.txt"
    call :checkError "Install Python Requirements"
) else (
    echo [WARN] requirements.txt not found; skipping.
)

if exist "%INSTALL_DIR%\repo\pygpt-MHP" (
    "%VENV_PY%" -m pip install -e "%INSTALL_DIR%\repo\pygpt-MHP"
    call :checkError "Install pygpt-MHP"
) else (
    echo [INFO] repo\pygpt-MHP not found; skipping editable install.
)

if exist "%INSTALL_DIR%\sync_pygpt_structure.py" (
    "%VENV_PY%" "%INSTALL_DIR%\sync_pygpt_structure.py"
    call :checkError "Sync submodule structure"
)

if exist "%INSTALL_DIR%\scripts\check_inter_program_connectivity.py" (
    "%VENV_PY%" "%INSTALL_DIR%\scripts\check_inter_program_connectivity.py"
    call :checkError "Inter-program connectivity"
)

goto :eof

:showLicenseGui
if "%SKIP_LICENSE_GUI%"=="1" (
    echo [INFO] Skipping license GUI (--skip-license-gui)
    goto :eof
)
if "%ACCEPT_LICENSE%"=="1" (
    echo [INFO] License accepted (--accept-license); skipping GUI
    goto :eof
)
if "%NON_INTERACTIVE%"=="1" (
    echo [INFO] Non-interactive mode; skipping license GUI
    goto :eof
)

if exist "%INSTALL_DIR%\src\license_gui.py" (
    echo Displaying license agreement...
    "%VENV_PY%" "%INSTALL_DIR%\src\license_gui.py"
    REM GUI may fail in some environments; do not hard-fail install
) else (
    echo [INFO] License GUI script not found; skipping.
)
goto :eof

:writeMetadata
set "META=%INSTALL_DIR%\.hueyos_install.env"
echo Writing install metadata: "%META%"

> "%META%" echo INSTALL_DIR=%INSTALL_DIR%
>> "%META%" echo MEMORY_PATH=%MEMORY_PATH%
>> "%META%" echo PROFILE=%PROFILE%
>> "%META%" echo REPO_URL=%REPO_URL%
>> "%META%" echo INSTALLED_AT=%date% %time%

REM Save deps list if any
if exist "%DEPS_TMP%" (
    copy /y "%DEPS_TMP%" "%INSTALL_DIR%\.hueyos_choco_deps.installed" >nul 2>&1
    del /q "%DEPS_TMP%" >nul 2>&1
)

goto :eof
