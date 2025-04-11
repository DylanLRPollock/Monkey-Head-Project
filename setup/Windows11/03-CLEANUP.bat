@echo off
setlocal enabledelayedexpansion

:: Change to the script's own directory
cd /d "%~dp0"

:: Clear screen and set color
cls
color 0A
echo [****|     03_CLEANUP.bat - Cleanup Development Environment   |****]
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

:: Function to remove virtual environment
:removeVirtualEnv
echo Removing virtual environment...
if exist "repository\venv" (
    rmdir /S /Q "repository\venv"
    call :checkError "Removing Virtual Environment"
) else (
    echo No virtual environment found.
)
goto :eof

:: Function to remove cloned repository
:removeRepository
echo Removing cloned repository...
if exist "repository" (
    rmdir /S /Q "repository"
    call :checkError "Removing Cloned Repository"
) else (
    echo No cloned repository found.
)
goto :eof

:: Function to remove common directories (Optional)
:removeDirectories
echo Removing common directories...
if exist "%USERPROFILE%\Projects" (
    rmdir /S /Q "%USERPROFILE%\Projects"
    call :checkError "Removing Projects Directory"
) else (
    echo No Projects directory found.
)
if exist "%USERPROFILE%\Tools" (
    rmdir /S /Q "%USERPROFILE%\Tools"
    call :checkError "Removing Tools Directory"
) else (
    echo No Tools directory found.
)
goto :eof

:: Function to clear environment variables (Optional)
:clearEnvVariables
echo Clearing environment variables...
REM Uncomment and modify the following line to clear specific environment variables
REM setx PATH ""
goto :eof

:: Function to uninstall Chocolatey packages (Optional)
:uninstallChocolateyPackages
echo Uninstalling Chocolatey packages...
REM Uncomment and add Chocolatey packages to uninstall
REM choco uninstall -y git
REM call :checkError "Uninstalling Git"
REM choco uninstall -y nodejs
REM call :checkError "Uninstalling NodeJS"
REM choco uninstall -y vscode
REM call :checkError "Uninstalling VSCode"
REM Add more packages as needed
goto :eof

:: Function to remove temporary files
:removeTempFiles
echo Removing temporary files...
del /F /Q %TEMP%\*
call :checkError "Removing Temp Files"
goto :eof

:: Function to clear npm cache
:clearNpmCache
echo Clearing npm cache...
npm cache clean --force
call :checkError "Clearing NPM Cache"
goto :eof

:: Function to clear pip cache
:clearPipCache
echo Clearing pip cache...
pip cache purge
call :checkError "Clearing Pip Cache"
goto :eof

:: Function to remove Docker containers, images, and volumes (Optional)
:cleanupDocker
echo Cleaning up Docker...
docker system prune -a -f --volumes
call :checkError "Cleaning Up Docker"
goto :eof

:: Main Execution Flow
echo Ensuring script runs with administrative privileges...
call :ensureAdmin

echo Removing virtual environment...
call :removeVirtualEnv

echo Removing cloned repository...
call :removeRepository

echo Removing common directories (Optional)...
call :removeDirectories

echo Clearing environment variables (Optional)...
call :clearEnvVariables

echo Uninstalling Chocolatey packages (Optional)...
call :uninstallChocolateyPackages

echo Removing temporary files...
call :removeTempFiles

echo Clearing npm cache...
call :clearNpmCache

echo Clearing pip cache...
call :clearPipCache

echo Cleaning up Docker (Optional)...
call :cleanupDocker

echo [****| Cleanup complete! |****]
echo Logs can be found in "%~dp0error_log.txt"
pause
exit /b 0

endlocal