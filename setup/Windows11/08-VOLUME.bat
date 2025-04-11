@echo off
setlocal enabledelayedexpansion

:: Change to the script's own directory
cd /d "%~dp0"

:: Clear screen and set color
cls
color 0A
echo [****|     08_VOLUME.bat - Docker Volume Management   |****]
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
echo %date% %time% - Error: %1 failed with error code %errorlevel% >> "%~dp0volume_error_log.txt"
goto :eof

:: Function to install Docker if not already installed
:installDocker
echo Checking for Docker installation...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Docker...
    choco install -y docker-desktop
    call :checkError "Docker Installation"
) else (
    echo Docker is already installed.
)
goto :eof

:: Function to start Docker service
:startDocker
echo Starting Docker service...
sc start com.docker.service >nul 2>&1
call :checkError "Starting Docker Service"
goto :eof

:: Function to check Docker daemon status
:checkDockerDaemon
echo Checking Docker daemon status...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker daemon is not running. Attempting to start...
    start /B "Docker Daemon" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    timeout /t 10 >nul
docker info >nul 2>&1
if %errorlevel% neq 0 (
        echo Error: Docker daemon failed to start.
        call :checkError "Starting Docker Daemon"
    ) else (
        echo Docker daemon started successfully.
    )
) else (
    echo Docker daemon is running.
)
goto :eof

:: Function to create a Docker volume
:createVolume
set /p volumeName="Enter the name of the volume to create: "
if "%volumeName%"=="" (
    echo Volume name cannot be empty.
    pause
    exit /b 1
)
echo Creating Docker volume %volumeName%...
docker volume create %volumeName%
call :checkError "Creating Docker Volume"
goto :eof

:: Function to list all Docker volumes
:listVolumes
echo Listing all Docker volumes...
docker volume ls
call :checkError "Listing Docker Volumes"
goto :eof

:: Function to inspect a Docker volume
:inspectVolume
set /p volumeName="Enter the name of the volume to inspect: "
if "%volumeName%"=="" (
    echo Volume name cannot be empty.
    pause
    exit /b 1
)
echo Inspecting Docker volume %volumeName%...
docker volume inspect %volumeName%
call :checkError "Inspecting Docker Volume"
goto :eof

:: Function to remove a Docker volume
:removeVolume
set /p volumeName="Enter the name of the volume to remove: "
if "%volumeName%"=="" (
    echo Volume name cannot be empty.
    pause
    exit /b 1
)
echo Removing Docker volume %volumeName%...
docker volume rm %volumeName%
call :checkError "Removing Docker Volume"
goto :eof

:: Function to prune unused Docker volumes
:pruneVolumes
echo Pruning unused Docker volumes...
docker volume prune -f
call :checkError "Pruning Docker Volumes"
goto :eof

:: Function to back up a Docker volume (Optional)
:backupVolume
set /p volumeName="Enter the name of the volume to back up: "
if "%volumeName%"=="" (
    echo Volume name cannot be empty.
    pause
    exit /b 1
)
set /p backupDir="Enter the backup directory path: "
if "%backupDir%"=="" (
    echo Backup directory cannot be empty.
    pause
    exit /b 1
)
echo Backing up Docker volume %volumeName% to %backupDir%...
docker run --rm -v %volumeName%:/volume -v %backupDir%:/backup alpine tar czf /backup/%volumeName%.tar.gz -C /volume .
call :checkError "Backing Up Docker Volume"
goto :eof

:: Function to restore a Docker volume (Optional)
:restoreVolume
set /p volumeName="Enter the name of the volume to restore: "
if "%volumeName%"=="" (
    echo Volume name cannot be empty.
    pause
    exit /b 1
)
set /p backupFile="Enter the backup file path: "
if "%backupFile%"=="" (
    echo Backup file cannot be empty.
    pause
    exit /b 1
)
echo Restoring Docker volume %volumeName% from %backupFile%...
docker run --rm -v %volumeName%:/volume -v %backupFile%:/backup alpine sh -c "rm -rf /volume/* && tar xzf /backup/%backupFile% -C /volume"
call :checkError "Restoring Docker Volume"
goto :eof

:: Function to log volume management steps
:logVolumeStep
echo Logging volume management step: %1
echo %DATE% %TIME% - %1 >> volume_log.txt
goto :eof

:: Ensure the script runs with administrative privileges
call :ensureAdmin

:: Install Docker if not already installed
call :installDocker

:: Start Docker service
call :startDocker

:: Check Docker daemon status
call :checkDockerDaemon

:menu
cls
echo [****|     Docker Volume Management   |****]
echo [1] Create a Docker Volume
echo [2] List Docker Volumes
echo [3] Inspect a Docker Volume
echo [4] Remove a Docker Volume
echo [5] Prune Unused Docker Volumes
echo [6] Back Up a Docker Volume
echo [7] Restore a Docker Volume
echo [E] Exit
echo.
set /p action="Please select an option (1-7, E to exit): "
if "%action%"=="1" goto createVolume
if "%action%"=="2" goto listVolumes
if "%action%"=="3" goto inspectVolume
if "%action%"=="4" goto removeVolume
if "%action%"=="5" goto pruneVolumes
if "%action%"=="6" goto backupVolume
if "%action%"=="7" goto restoreVolume
if /i "%action%"=="E" goto end
echo Invalid selection, please try again.
pause
goto menu

:end
echo [****| Docker volume management complete! |****]
pause
exit /b 0
