@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "pygpt-update.bat" %*
exit /b %errorlevel%
