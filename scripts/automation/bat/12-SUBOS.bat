@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "12-SUBOS.bat" %*
exit /b %errorlevel%
