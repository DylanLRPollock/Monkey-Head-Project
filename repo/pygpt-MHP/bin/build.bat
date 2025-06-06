# ==================================================  #
# This file is a part of the 'Monkey Head Project'                                       #
# Website:   https://dlrp.ca                                                                            #
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project    #
# License:   https://opensource.org/license/gpl-3-0                                 #
# Overseen By:   Dylan L.R. Pollock                                                             #
# Updated: 06.05.2025                                                                                 #
# ================================================== #
REM Set variables
SET BinDir=%CD%
SET BuildDir=%CD%\..\dist\Windows
SET ProjectDir=%CD%\..

REM Build app
cd %ProjectDir%
call venv\Scripts\activate
call pip install -r requirements.txt
call pyinstaller --noconfirm windows.spec

REM Copy ffmpg
copy "%BinDir%\ffmpeg.exe" "%BuildDir%\"
copy "%BinDir%\ffplay.exe" "%BuildDir%\"
copy "%BinDir%\ffprobe.exe" "%BuildDir%\"

