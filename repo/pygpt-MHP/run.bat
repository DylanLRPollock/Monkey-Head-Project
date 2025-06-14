# ==================================================  #
# This file is a part of the 'Monkey Head Project'                                       #
# Website:   https://dlrp.ca                                                                            #
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project    #
# License:   https://opensource.org/license/gpl-3-0                                 #
# Overseen By:   Dylan L.R. Pollock                                                             #
# Updated: 06.05.2025                                                                                 #
# ================================================== #
:: This script is used to run the app using the virtual environment
@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "ACTIVATE=%SCRIPT_DIR%venv\Scripts\activate.bat"
pushd "%SCRIPT_DIR%"
if not exist "%ACTIVATE%" (
    echo Virtual environment not found. Please run install.bat first.
    popd
    endlocal
    exit /b 1
)
call "%ACTIVATE%"
call python run.py %*
popd
endlocal
