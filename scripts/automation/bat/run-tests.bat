@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "run-tests.bat" %*
exit /b %errorlevel%
