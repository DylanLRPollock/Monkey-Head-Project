@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "04-TERMINAL.bat" %*
exit /b %errorlevel%
