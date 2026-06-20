@echo off
call "%~dp0_dispatch.bat" :run_memory_bat "shortcut.bat" %*
exit /b %errorlevel%
