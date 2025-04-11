@echo off
setlocal enabledelayedexpansion

:: Change to the script's own directory
cd /d "%~dp0"

:: Clear screen and set color
cls
color 0A
echo [****|     13_NANOOS.bat - NanoOS Setup and Configuration   |****]
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
echo %date% %time% - Error: %1 failed with error code %errorlevel% >> "%~dp0nanoos_error_log.txt"
goto :eof

:: Function to verify internet connectivity
:verifyInternet
echo Verifying internet connectivity...
ping -n 1 google.com >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: No internet connectivity.
    call :logError "Internet Connectivity"
    pause
    exit /b %errorlevel%
) else (
    echo Internet connectivity verified.
)
goto :eof

:: Function to check if a software is installed
:checkSoftware
echo Checking for %1 installation...
where %1 >nul 2>&1
if %errorlevel% neq 0 (
    echo %1 is not installed. Installing %1...
    %2
    call :checkError "Installing %1"
) else (
    echo %1 is already installed.
)
goto :eof

:: Function to check software version
:checkSoftwareVersion
echo Checking %1 version...
%1 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %1 version check failed.
    call :logError "%1 Version Check"
) else (
    echo %1 version: 
    %1 --version
)
goto :eof

:: Function to install required software
:installSoftware
echo Installing required software...
call :checkSoftware "git" "choco install -y git"
call :checkSoftwareVersion "git"
call :checkSoftware "node" "choco install -y nodejs"
call :checkSoftwareVersion "node"
REM Add more software checks and installations as needed
goto :eof

:: Function to configure system settings
:configureSystem
echo Configuring system settings...
REM Add commands to configure system settings
REM For example, setting environment variables:
setx NANOOS_ENV_VAR "NanoOSValue"
call :checkError "Setting Environment Variables"
goto :eof

:: Function to create necessary directories
:createDirectories
echo Creating necessary directories...
REM Add commands to create necessary directories
REM For example:
if not exist "C:\NanoOSData" mkdir C:\NanoOSData
call :checkError "Creating Directories"
goto :eof

:: Function to update the system
:updateSystem
echo Updating the system...
choco upgrade all -y
call :checkError "Updating System"
goto :eof

:: Function to clean up temporary files
:cleanupTempFiles
echo Cleaning up temporary files...
del /F /Q %TEMP%\*
call :checkError "Cleaning Up Temporary Files"
goto :eof

:: Function to restart necessary services
:restartServices
echo Restarting necessary services...
REM Add commands to restart necessary services
REM For example:
REM net stop wuauserv && net start wuauserv
call :checkError "Restarting Services"
goto :eof

:: Function to check system health
:checkSystemHealth
echo Checking system health...
REM Add commands to check system health
REM For example, checking disk space:
wmic logicaldisk get size,freespace,caption
call :checkError "Checking System Health"
goto :eof

:: Function to log setup steps
:logSetupStep
echo Logging setup step: %1
echo %DATE% %TIME% - %1 >> "%~dp0nanoos_log.txt"
goto :eof

:: Ensure the script runs with administrative privileges
call :ensureAdmin

:: Verify internet connectivity
call :verifyInternet

:: Log setup step
call :logSetupStep "Installing Software"

:: Install required software
call :installSoftware

:: Log setup step
call :logSetupStep "Configuring System Settings"

:: Configure system settings
call :configureSystem

:: Log setup step
call :logSetupStep "Creating Directories"

:: Create necessary directories
call :createDirectories

:: Log setup step
call :logSetupStep "Updating System"

:: Update the system
call :updateSystem

:: Log setup step
call :logSetupStep "Cleaning Up Temporary Files"

:: Clean up temporary files
call :cleanupTempFiles

:: Log setup step
call :logSetupStep "Restarting Services"

:: Restart necessary services
call :restartServices

:: Log setup step
call :logSetupStep "Checking System Health"

:: Check system health
call :checkSystemHealth

echo [****| NanoOS setup and configuration complete! |****]
pause
exit /b 0

endlocal