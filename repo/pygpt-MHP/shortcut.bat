# ==================================================  #
# This file is a part of the 'Monkey Head Project'                                       #
# Website:   https://dlrp.ca                                                                            #
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project    #
# License:   https://opensource.org/license/gpl-3-0                                 #
# Overseen By:   Dylan L.R. Pollock                                                             #
# Updated: 06.07.2025                                                                                 #
# ================================================== #
:: This script is used to run the app using the virtual environment
@echo off
cd /d "%~dp0"
call venv\Scripts\activate
call python run.py %*
