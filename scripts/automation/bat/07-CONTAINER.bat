@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "07-CONTAINER.bat" %*
exit /b %errorlevel%
