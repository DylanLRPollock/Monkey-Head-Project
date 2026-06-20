@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "01-FULL.bat" %*
exit /b %errorlevel%
