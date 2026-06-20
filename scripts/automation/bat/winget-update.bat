@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "winget-update.bat" %*
exit /b %errorlevel%
