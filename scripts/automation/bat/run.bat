@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "run.bat" %*
exit /b %errorlevel%
