@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "09-KUBERNETES.bat" %*
exit /b %errorlevel%
