# ==================================================  #
# This file is a part of the 'Monkey Head Project'                                       #
# Website:   https://dlrp.ca                                                                            #
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project    #
# License:   https://opensource.org/license/gpl-3-0                                 #
# Overseen By:   Dylan L.R. Pollock                                                             #
# Updated: 06.05.2025                                                                                 #
# ================================================== #
@echo off
setlocal
set "SCRIPT_DIR=%~dp0"

:: Create the virtual environment if it doesn't exist
if not exist "%SCRIPT_DIR%venv" (
    python -m venv "%SCRIPT_DIR%venv" || exit /b 1
)

set "ACTIVATE=%SCRIPT_DIR%venv\Scripts\activate.bat"
pushd "%SCRIPT_DIR%"
call "%ACTIVATE%"
python -m pip install --upgrade pip
pip install -r requirements.txt

call python run.py %*
popd
endlocal
