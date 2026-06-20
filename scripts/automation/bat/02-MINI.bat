@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "02-MINI.bat" %*
exit /b %errorlevel%
