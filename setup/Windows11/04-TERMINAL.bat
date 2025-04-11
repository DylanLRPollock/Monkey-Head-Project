@echo off
setlocal enabledelayedexpansion

:: Change to the script's own directory
cd /d "%~dp0"

:: Clear screen and set color
cls
color 0A
echo [****|     04_TERMINAL.bat - Terminal Setup and Configuration   |****]
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

:: Function to install Windows Terminal if not already installed
:installTerminal
echo Checking for Windows Terminal...
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe" (
    echo Windows Terminal is already installed.
) else (
    echo Installing Windows Terminal...
    choco install -y microsoft-windows-terminal
    call :checkError "Windows Terminal Installation"
)
goto :eof

:: Function to create default terminal settings if settings file does not exist
:createDefaultSettings
echo Checking for terminal settings file...
if not exist "terminal-settings.json" (
    echo Creating default terminal settings...
    (
        echo {
        echo "profiles": {
        echo "defaults": {},
        echo "list": []
        echo },
        echo "schemes": [],
        echo "actions": [],
        echo "globals": {}
        echo }
    ) > "terminal-settings.json"
    call :checkError "Creating Default Terminal Settings"
) else (
    echo Custom terminal settings file found.
)
goto :eof

:: Function to back up existing terminal settings
:backupExistingSettings
echo Would you like to back up existing terminal settings? (Y/N)
set /p backupChoice=
if /i "%backupChoice%"=="Y" (
    echo Backing up existing terminal settings...
    if exist "%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json" (
        copy /Y "%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json" "%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings_backup.json"
        call :checkError "Backing Up Existing Terminal Settings"
    ) else (
        echo No existing terminal settings found to back up.
    )
) else (
    echo Skipping backup of existing terminal settings.
)
goto :eof

:: Function to configure Windows Terminal settings
:configureTerminal
echo Configuring Windows Terminal settings...
copy /Y "terminal-settings.json" "%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
call :checkError "Copying Terminal Settings"
goto :eof

:: Function to install optional terminal tools and extensions
:installOptionalTools
echo Would you like to install optional terminal tools and extensions? (Y/N)
set /p toolsChoice=
if /i "%toolsChoice%"=="Y" (
    echo Installing optional terminal tools and extensions...
    REM Uncomment and modify the following lines to install additional tools and extensions
    REM choco install -y posh-git
    REM call :checkError "Posh-Git Installation"
    REM choco install -y oh-my-posh
    REM call :checkError "Oh-My-Posh Installation"
    REM Install PowerShell modules if needed
    REM powershell -Command "Install-Module -Name PSReadLine -Force -SkipPublisherCheck"
    REM call :checkError "PSReadLine Installation"
    REM powershell -Command "Install-Module -Name Pester -Force -SkipPublisherCheck"
    REM call :checkError "Pester Installation"
) else (
    echo Skipping installation of optional tools and extensions.
)
goto :eof

:: Function to verify installation
:verifyInstallation
echo Verifying Windows Terminal installation...
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe" (
    echo Windows Terminal installed successfully.
) else (
    echo Error: Windows Terminal installation failed.
    call :logError "Windows Terminal Installation Verification"
    pause
    exit /b 1
)
goto :eof

:: Ensure the script runs with administrative privileges
call :ensureAdmin

:: Install Windows Terminal
call :installTerminal

:: Create default terminal settings if necessary
call :createDefaultSettings

:: Back up existing terminal settings
call :backupExistingSettings

:: Configure Windows Terminal settings
call :configureTerminal

:: Install optional terminal tools and extensions
call :installOptionalTools

:: Verify installation
call :verifyInstallation

echo [****| Terminal setup complete! |****]
echo Logs can be found in "%~dp0error_log.txt"
pause
exit /b 0

endlocal