@echo off
setlocal EnableExtensions

if "%~1"=="" goto :usage
if /I "%~1"=="help" goto :usage
if /I "%~1"=="--help" goto :usage
if /I "%~1"=="/?" goto :usage
if "%~2"=="" goto :usage

where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ffmpeg is not available on PATH.
    exit /b 1
)

set "INPUT_FILE=%~1"
set "OUTPUT_DIR=%~2"
set "BITRATE=%~3"
if not defined BITRATE set "BITRATE=320k"

if not exist "%INPUT_FILE%" (
    echo [ERROR] Input file not found: "%INPUT_FILE%"
    exit /b 1
)
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%" >nul 2>&1

for %%I in ("%INPUT_FILE%") do set "OUTPUT_FILE=%OUTPUT_DIR%\%%~nI.mp3"

ffmpeg -y -i "%INPUT_FILE%" -vn -c:a libmp3lame -b:a %BITRATE% "%OUTPUT_FILE%"
exit /b %errorlevel%

:usage
echo Usage: %~nx0 INPUT_MKV OUTPUT_DIR [BITRATE]
echo.
echo Example:
echo   %~nx0 movie.mkv audio 320k
exit /b 0
