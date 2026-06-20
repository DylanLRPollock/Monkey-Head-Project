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

:resolve_python
setlocal EnableExtensions
set "root=%~1"
if defined root if exist "%root%\venv\Scripts\python.exe" (
    endlocal & set "%~2=%root%\venv\Scripts\python.exe" & exit /b 0
)
where python >nul 2>&1
if %errorlevel% neq 0 (
    endlocal & exit /b 1
)
endlocal & set "%~2=python" & exit /b 0

:timestamp
setlocal EnableExtensions
set "stamp="
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "stamp=%%I"
if not defined stamp (
    set "stamp=%DATE:/=-%_%TIME::=-%"
    set "stamp=%stamp: =0%"
)
for %%I in ("!stamp!") do endlocal & set "%~1=%%~I" & exit /b 0

:compose
setlocal EnableExtensions
set "compose_file=%~1"
set "project_name=%~2"
if not exist "%compose_file%" (
    echo [ERROR] Docker Compose file not found: "%compose_file%"
    endlocal & exit /b 1
)
shift /1
shift /1
docker compose version >nul 2>&1
if %errorlevel%==0 (
    docker compose -p "%project_name%" -f "%compose_file%" %*
    set "exit_code=%errorlevel%"
    endlocal & exit /b %exit_code%
)
docker-compose --version >nul 2>&1
if %errorlevel%==0 (
    docker-compose -p "%project_name%" -f "%compose_file%" %*
    set "exit_code=%errorlevel%"
    endlocal & exit /b %exit_code%
)
echo [ERROR] Neither "docker compose" nor "docker-compose" is available.
endlocal & exit /b 1
