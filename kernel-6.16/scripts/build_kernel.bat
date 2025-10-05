@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "DEFAULT_VERSION=6.16.12"

if "%1"=="-h" goto :usage
if "%1"=="--help" goto :usage

set "VERSION=%DEFAULT_VERSION%"
if not "%1"=="" (
  if not "%1"=="--" (
    set "VERSION=%1"
    shift
  )
)

set "PYTHON=%PYTHON%"
if "%PYTHON%"=="" set "PYTHON=python3"

"%PYTHON%" "%SCRIPT_DIR%build_kernel.py" --version "%VERSION%" %*
exit /b %errorlevel%

:usage
  echo Usage: %~n0 ^[version^] ^[-- ^<extra args^>^]
  echo.
  echo version      Optional kernel version ^(defaults to %DEFAULT_VERSION%^).
  echo extra args   Additional arguments passed to build_kernel.py.
  echo.
  echo Example:
  echo   %~n0 6.16.12 -- -j16
  exit /b 0
