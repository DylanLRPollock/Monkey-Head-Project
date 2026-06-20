@echo off
if "%~1"=="" exit /b 0
set "_label=%~1"
shift
goto %_label%

:resolve_repo_root
setlocal EnableExtensions EnableDelayedExpansion
set "current=%~2"
if not defined current set "current=%~dp0"
for %%I in ("!current!") do set "current=%%~fI"
:resolve_repo_root_loop
if exist "!current!\pyproject.toml" if exist "!current!\run.py" (
    for %%I in ("!current!") do endlocal & set "%~1=%%~fI" & exit /b 0
)
for %%I in ("!current!\..") do set "parent=%%~fI"
if /I "!parent!"=="!current!" (
    endlocal & exit /b 1
)
set "current=!parent!"
goto :resolve_repo_root_loop

:run_memory_bat
setlocal EnableExtensions
set "script_name=%~1"
shift
call "%~dp0_dispatch.bat" :resolve_repo_root REPO_ROOT "%~dp0"
if errorlevel 1 (
    echo [ERROR] Could not locate the Huey repository root from "%~dp0".
    endlocal & exit /b 1
)
set "target=%REPO_ROOT%\src\huey\memory\BAT\%script_name%"
if not exist "%target%" (
    echo [ERROR] Remembered batch script not found: "%target%"
    endlocal & exit /b 1
)
call "%target%" %*
set "exit_code=%errorlevel%"
endlocal & exit /b %exit_code%
