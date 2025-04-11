@echo off
setlocal enabledelayedexpansion

:: Change to the script's own directory
cd /d "%~dp0"

:: Clear screen and set color
cls
color 0A
echo [****|     05_UPDATE.bat - Update Installed Packages and Tools   |****]
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
echo %date% %time% - Error: %1 failed with error code %errorlevel% >> "%~dp0error_log.txt"
goto :eof

:: Function to update Chocolatey itself
:updateChocolatey
echo Updating Chocolatey...
choco upgrade chocolatey -y
call :checkError "Chocolatey Update"
goto :eof

:: Function to update all installed Chocolatey packages
:updateChocoPackages
echo Updating all installed Chocolatey packages...
choco upgrade all -y
call :checkError "Chocolatey Packages Update"
goto :eof

:: Function to update npm global packages
:updateNpmPackages
echo Updating npm global packages...
npm update -g
call :checkError "NPM Global Packages Update"
goto :eof

:: Function to update pip packages
:updatePipPackages
echo Updating pip packages...
python -m pip install --upgrade pip
call :checkError "Pip Update"
pip list --outdated --format=freeze | findstr /v "^\-e" | for /f "delims==" %%i in ('more') do python -m pip install -U %%i
call :checkError "Pip Packages Update"
goto :eof

:: Function to update VSCode extensions
:updateVSCodeExtensions
echo Updating VSCode extensions...
for /f %%i in ('code --list-extensions') do code --install-extension %%i
call :checkError "VSCode Extensions Update"
goto :eof

:: Function to update PowerShell modules
:updatePSModules
echo Updating PowerShell modules...
powershell -Command "Get-InstalledModule | ForEach-Object { Update-Module -Name $_.Name -Force }"
call :checkError "PowerShell Modules Update"
goto :eof

:: Function to update Docker images
:updateDockerImages
echo Updating Docker images...
docker images --format "{{.Repository}}:{{.Tag}}" | findstr /v "<none>" | for /f "delims=" %%i in ('more') do docker pull %%i
call :checkError "Docker Images Update"
goto :eof

:: Ensure the script runs with administrative privileges
call :ensureAdmin

:: Update Chocolatey itself
call :updateChocolatey

:: Update all installed Chocolatey packages
call :updateChocoPackages

:: Update npm global packages
call :updateNpmPackages

:: Update pip packages
call :updatePipPackages

:: Update VSCode extensions
call :updateVSCodeExtensions

:: Update PowerShell modules
call :updatePSModules

:: Update Docker images
call :updateDockerImages

echo [****| Updates complete! |****]
echo Logs can be found in "%~dp0error_log.txt"
pause
exit /b 0

endlocal