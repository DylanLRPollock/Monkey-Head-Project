@echo off
REM ==================================================
REM This file is a part of the 'Monkey Head Project'
REM Website:   https://dlrp.ca
REM GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
REM License:   https://opensource.org/license/gpl-3-0
REM Overseen By:   Dylan L.R. Pollock
REM Updated: 06.09.2025
REM ==================================================

set SCRIPT_DIR=%~dp0
set UNINSTALL_SCRIPT=%SCRIPT_DIR%setup\Windows11\03-CLEANUP.bat

call "%UNINSTALL_SCRIPT%"
