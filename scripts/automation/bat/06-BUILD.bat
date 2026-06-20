@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "06-BUILD.bat" %*
exit /b %errorlevel%
