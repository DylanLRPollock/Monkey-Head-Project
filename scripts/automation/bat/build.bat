@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "build.bat" %*
exit /b %errorlevel%
