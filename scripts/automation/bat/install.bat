@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "install.bat" %*
exit /b %errorlevel%
