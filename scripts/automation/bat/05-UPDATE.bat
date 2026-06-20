@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "05-UPDATE.bat" %*
exit /b %errorlevel%
