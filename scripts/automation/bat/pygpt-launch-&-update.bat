@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "pygpt-launch-&-update.bat" %*
exit /b %errorlevel%
