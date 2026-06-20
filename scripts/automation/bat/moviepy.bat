@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "moviepy.bat" %*
exit /b %errorlevel%
