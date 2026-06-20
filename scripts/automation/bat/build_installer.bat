@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "build_installer.bat" %*
exit /b %errorlevel%
