@echo off
REM Monkey Head Project
REM By: Dylan L.R. Pollock
REM www.dlrp.ca
REM HueyOS: Windows Uninstall script (unified)

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
set "REMOVE_MEMORY=0"
set "PURGE_DEPS=0"
set "DOCKER_PRUNE=0"
set "YES=0"

REM ----------------------------
REM Arg parsing
REM ----------------------------
:parseArgs
if "%~1"=="" goto :argsDone

if /I "%~1"=="--help"            goto :usage
if /I "%~1"=="-h"                goto :usage

if /I "%~1"=="--install-dir"     ( set "INSTALL_DIR=%~2" & shift & shift & goto :parseArgs )

if /I "%~1"=="--remove-memory"   ( set "REMOVE_MEMORY=1" & shift & goto :parseArgs )
if /I "%~1"=="--purge-deps"      ( set "PURGE_DEPS=1" & shift & goto :parseArgs )
if /I "%~1"=="--docker-prune"    ( set "DOCKER_PRUNE=1" & shift & goto :parseArgs )
if /I "%~1"=="--yes"             ( set "YES=1" & shift & goto :parseArgs )

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

if not exist "%INSTALL_DIR%" (
    echo [ERROR] Install directory not found: "%INSTALL_DIR%"
    exit /b 1
)

REM Load metadata if present
set "META=%INSTALL_DIR%\.hueyos_install.env"
if exist "%META%" (
    call :loadMetadata "%META%"
)

REM Determine memory path
if defined MEMORY_PATH (
    set "MEM_PATH=%MEMORY_PATH%"
) else (
    set "MEM_PATH=%INSTALL_DIR%\memory"
)

REM ----------------------------
REM Elevation decision
REM - Uninstall from Program Files and/or purging deps typically needs admin
REM ----------------------------
set "NEEDS_ADMIN=0"
echo "%INSTALL_DIR%" | find /I "%ProgramFiles%" >nul 2>&1
if %errorlevel%==0 set "NEEDS_ADMIN=1"
if "%PURGE_DEPS%"=="1" set "NEEDS_ADMIN=1"
if "%DOCKER_PRUNE%"=="1" set "NEEDS_ADMIN=1"

if "%NEEDS_ADMIN%"=="1" call :ensureAdmin

REM ----------------------------
REM Preserve memory by default
REM ----------------------------
call :handleMemory

REM ----------------------------
REM Capture deps list before removing install dir
REM ----------------------------
set "DEPS_FILE=%INSTALL_DIR%\.hueyos_choco_deps.installed"
set "DEPS_COPY="
if "%PURGE_DEPS%"=="1" if exist "%DEPS_FILE%" (
    set "DEPS_COPY=%TEMP%\hueyos_choco_deps_uninstall_%RANDOM%%RANDOM%.txt"
    copy /y "%DEPS_FILE%" "%DEPS_COPY%" >nul 2>&1
)

REM ----------------------------
REM Remove install directory
REM ----------------------------
echo Removing installed files: "%INSTALL_DIR%"
rmdir /S /Q "%INSTALL_DIR%"
if %errorlevel% neq 0 (
    echo [WARN] Failed to fully remove install directory. You may need to delete it manually.
)

REM ----------------------------
REM Optional: purge dependencies that THIS installer added (explicit)
REM ----------------------------
if "%PURGE_DEPS%"=="1" (
    if "%YES%"=="0" (
        echo [ERROR] --purge-deps requires --yes (explicit confirmation).
        exit /b 2
    )
    call :purgeDeps "%DEPS_COPY%"
)

REM ----------------------------
REM Optional: docker prune (VERY destructive)
REM ----------------------------
if "%DOCKER_PRUNE%"=="1" (
    if "%YES%"=="0" (
        echo [ERROR] --docker-prune requires --yes (explicit confirmation).
        exit /b 2
    )
    call :dockerPrune
)

echo.
echo [****| Uninstall complete! |****]
pause
exit /b 0

REM ==================================================
REM Functions
REM ==================================================

:usage
echo.
echo Usage: %~nx0 [options]
echo.
echo   --install-dir PATH       Target install directory (auto-detected if omitted)
echo   --remove-memory          Delete memory directory instead of preserving it
echo   --purge-deps             Uninstall Chocolatey packages recorded as installed by install script
echo   --docker-prune           Run "docker system prune -a --volumes" (VERY destructive)
echo   --yes                    Required confirmation for --purge-deps and --docker-prune
echo.
exit /b 2

:logError
echo %date% %time% - Error: %~1 (exit=%errorlevel%)>> "%ERROR_LOG%"
goto :eof

:ensureAdmin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrative privileges...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -ArgumentList '%*' -Verb RunAs"
    exit /b 0
)
goto :eof

:loadMetadata
for /f "usebackq tokens=1,* delims==" %%A in ("%~1") do (
    set "%%A=%%B"
)
goto :eof

:handleMemory
if not exist "%MEM_PATH%" (
    echo [INFO] No memory directory found at "%MEM_PATH%".
    goto :eof
)

if "%REMOVE_MEMORY%"=="1" (
    echo Deleting memory directory: "%MEM_PATH%"
    rmdir /S /Q "%MEM_PATH%"
    goto :eof
)

REM Preserve memory by moving it out if it is inside the install dir
echo "%MEM_PATH%" | find /I "%INSTALL_DIR%" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Memory path is outside install dir; leaving in place: "%MEM_PATH%"
    goto :eof
)

for /f "delims=" %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%T"
set "BACKUP_ROOT=%LOCALAPPDATA%\MonkeyHeadProject"
set "BACKUP_PATH=%BACKUP_ROOT%\memory_backup_%TS%"

echo Preserving memory by moving it to:
echo   "%BACKUP_PATH%"

if not exist "%BACKUP_ROOT%" mkdir "%BACKUP_ROOT%" >nul 2>&1

move "%MEM_PATH%" "%BACKUP_PATH%" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Move failed; attempting copy+remove...
    robocopy "%MEM_PATH%" "%BACKUP_PATH%" /E >nul
    rmdir /S /Q "%MEM_PATH%" >nul 2>&1
)

goto :eof

:purgeDeps
set "FILE=%~1"
if not defined FILE (
    echo [WARN] No recorded deps file found. Skipping purge.
    goto :eof
)
if not exist "%FILE%" (
    echo [WARN] Recorded deps file missing: "%FILE%". Skipping purge.
    goto :eof
)

where choco >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Chocolatey not found; cannot purge deps automatically.
    goto :eof
)

echo Purging Chocolatey packages recorded as installed by installer...
for /f "usebackq delims=" %%P in ("%FILE%") do (
    if not "%%P"=="" (
        echo Uninstalling %%P...
        choco uninstall -y "%%P" >nul 2>&1
    )
)

del /q "%FILE%" >nul 2>&1
goto :eof

:dockerPrune
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] docker not found; skipping prune.
    goto :eof
)

echo Running Docker prune (this removes images/containers/volumes not in use)...
docker system prune -a -f --volumes
goto :eof
