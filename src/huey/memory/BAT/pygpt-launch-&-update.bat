@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
call "%SCRIPT_DIR%pygpt-update.bat"
if errorlevel 1 exit /b %errorlevel%
call "%SCRIPT_DIR%pygpt-launch.bat"
exit /b %errorlevel%
