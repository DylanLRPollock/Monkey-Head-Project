@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "pygpt-launch.bat" %*
exit /b %errorlevel%
