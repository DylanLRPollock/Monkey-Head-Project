@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "PROFILE=full"
set "RECREATE_VENV=0"
set "RUN_PULL=0"
set "PREVIEW_WINGET=0"
set "RUN_WINGET=0"
set "RUN_CHOCO=0"
set "RUN_DOCKER_IMAGES=0"
set "RUN_VSCODE_EXTS=0"
set "RUN_PS_MODULES=0"
set "YES=0"

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
if /I "%~1"=="--recreate-venv" (
    set "RECREATE_VENV=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--pull" (
    set "RUN_PULL=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--preview-winget" (
    set "PREVIEW_WINGET=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--winget-all" (
    set "RUN_WINGET=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--choco-all" (
    set "RUN_CHOCO=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--docker-images" (
    set "RUN_DOCKER_IMAGES=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--vscode-exts" (
    set "RUN_VSCODE_EXTS=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--ps-modules" (
    set "RUN_PS_MODULES=1"
    shift
    goto :parse_args
)
if /I "%~1"=="--yes" (
    set "YES=1"
    shift
    goto :parse_args
)
echo [ERROR] Unknown argument: %~1
goto :usage

:args_done
if "%RUN_WINGET%"=="1" if not "%YES%"=="1" (
    echo [ERROR] --winget-all requires --yes.
    exit /b 2
)
if "%RUN_CHOCO%"=="1" if not "%YES%"=="1" (
    echo [ERROR] --choco-all requires --yes.
    exit /b 2
)

call "%SCRIPT_DIR%_common.bat" :resolve_repo_root ROOT_DIR "%SCRIPT_DIR%"
if errorlevel 1 (
    echo [ERROR] Could not locate the repository root from "%SCRIPT_DIR%".
    exit /b 1
)

if "%RUN_PULL%"=="1" (
    where git >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] git was not found.
        exit /b 1
    )
    set "STATUS_FILE=%TEMP%\mhp_git_status_%RANDOM%%RANDOM%.txt"
    set "GIT_STATUS_SIZE=0"
    pushd "%ROOT_DIR%" >nul
    git status --porcelain > "%STATUS_FILE%"
    for %%F in ("%STATUS_FILE%") do (
        for %%A in (%%~zF) do set "GIT_STATUS_SIZE=%%A"
        del /Q "%%~fF" >nul 2>&1
    )
    if not "%GIT_STATUS_SIZE%"=="0" (
        popd >nul
        echo [ERROR] Local changes are present. Commit or stash them before using --pull.
        exit /b 1
    )
    git pull --recurse-submodules
    if errorlevel 1 (
        popd >nul
        exit /b 1
    )
    git submodule update --init --recursive
    set "EXIT_CODE=%errorlevel%"
    popd >nul
    if not "%EXIT_CODE%"=="0" exit /b %EXIT_CODE%
)

if "%RECREATE_VENV%"=="1" (
    call "%SCRIPT_DIR%install.bat" --profile %PROFILE% --skip-license-gui --recreate-venv
) else (
    call "%SCRIPT_DIR%install.bat" --profile %PROFILE% --skip-license-gui
)
if errorlevel 1 exit /b %errorlevel%

if "%PREVIEW_WINGET%"=="1" (
    where winget >nul 2>&1
    if errorlevel 1 (
        echo [WARN] winget is not available; skipping preview.
    ) else (
        winget upgrade
        if errorlevel 1 exit /b 1
    )
)

if "%RUN_WINGET%"=="1" (
    where winget >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] winget is not available.
        exit /b 1
    )
    winget upgrade --all --accept-source-agreements --accept-package-agreements
    if errorlevel 1 exit /b 1
)

if "%RUN_CHOCO%"=="1" (
    where choco >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Chocolatey is not available.
        exit /b 1
    )
    choco upgrade chocolatey -y
    if errorlevel 1 exit /b 1
    choco upgrade all -y
    if errorlevel 1 exit /b 1
)

if "%RUN_DOCKER_IMAGES%"=="1" (
    call "%SCRIPT_DIR%07-CONTAINER.bat" pull
    if errorlevel 1 exit /b %errorlevel%
)

if "%RUN_VSCODE_EXTS%"=="1" (
    where code >nul 2>&1
    if errorlevel 1 (
        echo [WARN] VS Code CLI is not available; skipping extension updates.
    ) else (
        for /f %%I in ('code --list-extensions') do code --install-extension %%I >nul 2>&1
    )
)

if "%RUN_PS_MODULES%"=="1" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-InstalledModule | ForEach-Object { Update-Module -Name $_.Name -Force }"
    if errorlevel 1 exit /b 1
)

echo.
echo [****| Update complete. |****]
exit /b 0

:usage
echo Usage: %~nx0 [options]
echo.
echo Default behavior: refresh the local virtual environment and reinstall the current repository dependencies.
echo.
echo Options:
echo   --profile full^|mini   Match the local install profile. Default: full.
echo   --recreate-venv        Rebuild the repository virtual environment first.
echo   --pull                 Update the git checkout when the working tree is clean.
echo   --preview-winget       Show available winget upgrades without installing them.
echo   --winget-all --yes     Install all available winget upgrades.
echo   --choco-all --yes      Install all available Chocolatey upgrades.
echo   --docker-images        Pull newer versions of the compose images.
echo   --vscode-exts          Reinstall all listed VS Code extensions.
echo   --ps-modules           Update installed PowerShell modules.
exit /b 0
