@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "EXIT.bat" %*
exit /b %errorlevel%
