@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "03-CLEANUP.bat" %*
exit /b %errorlevel%
