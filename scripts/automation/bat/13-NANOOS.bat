@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "13-NANOOS.bat" %*
exit /b %errorlevel%
