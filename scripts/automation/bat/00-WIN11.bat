@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "00-WIN11.bat" %*
exit /b %errorlevel%
