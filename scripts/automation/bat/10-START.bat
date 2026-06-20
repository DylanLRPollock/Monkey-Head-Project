@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "10-START.bat" %*
exit /b %errorlevel%
