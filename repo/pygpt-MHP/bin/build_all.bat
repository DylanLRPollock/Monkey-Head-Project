# ==================================================  #
# This file is a part of the 'Monkey Head Project'                                       #
# Website:   https://dlrp.ca                                                                            #
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project    #
# License:   https://opensource.org/license/gpl-3-0                                 #
# Overseen By:   Dylan L.R. Pollock                                                             #
# Updated: 06.05.2025                                                                                 #
# ================================================== #
@echo off

REM Set variables
SET CurrentDir=%CD%
SET SIGNTOOL=C:\Program Files (x86)\Microsoft SDKs\ClickOnce\SignTool

REM Build app
call build.bat

cd "%CurrentDir%"

"%SIGNTOOL%\signtool.exe" sign /t http://time.certum.pl "%CD%\..\dist\Windows\pygpt.exe"

REM Create installer
call build_installer.bat
"%SIGNTOOL%\signtool.exe" sign /t http://time.certum.pl "%CD%\..\dist\pygpt-%ProductVersion%.msi"
