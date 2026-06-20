@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "_common.bat" %*
exit /b %errorlevel%
