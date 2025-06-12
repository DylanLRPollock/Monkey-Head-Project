@echo off
REM ==================================================
REM This file is a part of the 'Monkey Head Project'
REM Website:   https://dlrp.ca
REM GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
REM License:   https://opensource.org/license/gpl-3-0
REM Overseen By:   Dylan L.R. Pollock
REM Updated: 06.11.2025
REM ==================================================

set SCRIPT_DIR=%~dp0
set INSTALL_SCRIPT=%SCRIPT_DIR%setup\Windows11\01-FULL.bat

call "%INSTALL_SCRIPT%"
echo.
echo ***********************************************
echo   Thank you for supporting the Monkey Head Project!
echo   We hope you enjoy using it.
echo ***********************************************
