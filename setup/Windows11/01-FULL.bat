# ==================================================  #
# This file is a part of the 'Monkey Head Project'                                       #
# Website:   https://dlrp.ca                                                                            #
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project    #
# License:   https://opensource.org/license/gpl-3-0                                 #
# Overseen By:   Dylan L.R. Pollock                                                             #
# Updated: 06.11.2025                                                                                 #
# ================================================== #
@echo off
setlocal enabledelayedexpansion

:: Default installation directory
set "INSTALL_DIR=%ProgramFiles%\Monkey-Head-Project"

:: Change to the script's own directory
cd /d "%~dp0"

:: Clear screen and set color
cls
color 0A
echo [****|     01_FULL.bat - Full Development Environment Setup   |****]
echo.

:: Function to ensure the script is running with administrative privileges
:ensureAdmin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Please run this script as an administrator.
    pause
    exit /b %errorlevel%
)
goto :eof

:: Function to check the last command and exit if it failed
:checkError
if %errorlevel% neq 0 (
    echo Error: %1 failed with error code %errorlevel%.
    call :logError "%1"
    pause
    exit /b %errorlevel%
)
goto :eof

:: Function to log errors
:logError
echo %date% %time% - Error: %1 failed with error code %errorlevel% >> error_log.txt
goto :eof

:: Function to perform initial system checks
:systemCheck
echo Performing system checks...
REM Check for Windows version (Windows 10 or 11)
ver | find "10.0" >nul
call :checkError "Windows version check"
REM Check for available disk space
for /f "tokens=3" %%a in ('dir /-C %SystemDrive% ^| findstr /R "bytes free$"') do set FreeSpace=%%a
echo Free space on %SystemDrive%: %FreeSpace%
REM Check for internet connectivity
ping -n 1 google.com >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: No internet connection detected.
    call :logError "Internet Connectivity Check"
    pause
    exit /b %errorlevel%
)
REM Check for required software (e.g., PowerShell, Git)
powershell -command "Get-Command git -ErrorAction SilentlyContinue" >nul
call :checkError "Git Availability Check"
REM Add any other necessary checks here
goto :eof

:: Function to install Chocolatey if not already installed
:installChocolatey
if exist "%ProgramData%\chocolatey\bin\choco.exe" (
    echo Chocolatey is already installed.
) else (
    echo Installing Chocolatey...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
    call :checkError "Chocolatey Installation"
)
goto :eof

:: Function to update system files and health
:updateSystem
echo Updating system...
powershell -Command "Start-Process 'powershell' -ArgumentList 'sfc /scannow' -Verb RunAs"
call :checkError "sfc /scannow"
powershell -Command "Start-Process 'powershell' -ArgumentList 'DISM /Online /Cleanup-Image /RestoreHealth' -Verb RunAs"
call :checkError "DISM RestoreHealth"
goto :eof

:: Function to install common tools
:installCommonTools
echo Installing common tools...
choco install -y git
call :checkError "Git Installation"
choco install -y nodejs
call :checkError "NodeJS Installation"
choco install -y vscode
call :checkError "VSCode Installation"
goto :eof

:: Function to install additional tools
:installAdditionalTools
echo Installing additional tools...
choco install -y python
call :checkError "Python Installation"
choco install -y docker-desktop
call :checkError "Docker Installation"
goto :eof

:: Function to clone the repository
:cloneRepository
echo Cloning repository...
if exist "%INSTALL_DIR%" (
    rmdir /S /Q "%INSTALL_DIR%"
)
mkdir "%INSTALL_DIR%"
cd "%INSTALL_DIR%"
git clone --recurse-submodules https://github.com/DylanLRPollock/Monkey-Head-Project.git .
call :checkError "Git Clone"
git submodule update --init --recursive
goto :eof

:: Function to set up Python environment
:setupPythonEnv
echo Setting up Python environment...
cd "%INSTALL_DIR%"
python -m venv venv
call :checkError "Python Virtual Environment Setup"
venv\Scripts\activate
call :checkError "Activate Python Virtual Environment"
pip install -r requirements.txt
call :checkError "Install Python Requirements"
pip install -e repo\pygpt-MHP
call :checkError "Install pygpt-MHP"
goto :eof

:: Function to configure Git
:configureGit
echo Configuring Git...
git config --global user.name "Your Name"
call :checkError "Git Config Username"
git config --global user.email "your.email@example.com"
call :checkError "Git Config Email"
goto :eof

:: Function to create common directories
:createDirectories
echo Creating common directories...
mkdir %USERPROFILE%\Projects
call :checkError "Creating Projects Directory"
mkdir %USERPROFILE%\Tools
call :checkError "Creating Tools Directory"
goto :eof

:: Function to update environment variables (Optional)
:updateEnvVariables
echo Updating environment variables...
setx PATH "%PATH%;%USERPROFILE%\Tools"
call :checkError "Updating PATH Environment Variable"
goto :eof

:: Function to install optional tools
:installOptionalTools
echo Installing optional tools...
REM Uncomment the tools you need
choco install -y postman
call :checkError "Postman Installation"
choco install -y slack
call :checkError "Slack Installation"
choco install -y zoom
call :checkError "Zoom Installation"
choco install -y 7zip
call :checkError "7zip Installation"
choco install -y wget
call :checkError "Wget Installation"
choco install -y curl
call :checkError "Curl Installation"
choco install -y terraform
call :checkError "Terraform Installation"
choco install -y kubectl
call :checkError "kubectl Installation"
choco install -y minikube
call :checkError "Minikube Installation"
choco install -y awscli
call :checkError "AWS CLI Installation"
choco install -y azure-cli
call :checkError "Azure CLI Installation"
goto :eof

:: Function to display license GUI
:showLicenseGui
echo Displaying license agreement...
call venv\Scripts\activate
python src\license_gui.py
if %errorlevel% neq 0 echo License dialog could not be displayed
goto :eof

:: Main Execution Flow
echo Ensuring script runs with administrative privileges...
call :ensureAdmin

echo Performing initial system checks...
call :systemCheck

echo Installing Chocolatey if not already installed...
call :installChocolatey

echo Updating system files and health...
call :updateSystem

echo Installing common tools...
call :installCommonTools

echo Installing additional tools...
call :installAdditionalTools

echo Cloning the repository...
call :cloneRepository

echo Setting up Python environment...
call :setupPythonEnv

echo Configuring Git...
call :configureGit

echo Creating common directories...
call :createDirectories

echo Updating environment variables...
call :updateEnvVariables

echo Installing optional tools...
call :installOptionalTools

echo Displaying license agreement...
call :showLicenseGui

echo [****| Full setup complete! |****]
echo.
echo ***********************************************
echo   Thank you for supporting the Monkey Head Project!
echo   We hope you enjoy using it.
echo ***********************************************
pause
exit /b 0

endlocal
