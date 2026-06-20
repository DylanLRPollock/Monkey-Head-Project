@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "11-HOSTOS.bat" %*
exit /b %errorlevel%
