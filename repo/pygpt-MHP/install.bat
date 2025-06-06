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

:: Create the virtual environment if it doesn't exist
if not exist venv (
    python -m venv venv || exit /b 1
)

call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

call python run.py %*

endlocal
