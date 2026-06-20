@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "git-install.bat" %*
exit /b %errorlevel%
