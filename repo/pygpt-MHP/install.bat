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
