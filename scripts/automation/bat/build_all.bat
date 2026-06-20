@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "build_all.bat" %*
exit /b %errorlevel%
