@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "uninstall.bat" %*
exit /b %errorlevel%
