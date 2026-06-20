@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "make.bat" %*
exit /b %errorlevel%
