@echo off
setlocal enabledelayedexpansion

:: Change to the script's own directory
cd /d "%~dp0"

:: Clear screen and set color
cls
color 0A
echo [****|     07_CONTAINER.bat - Docker Container Management   |****]
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
echo %date% %time% - Error: %1 failed with error code %errorlevel% >> "%~dp0docker_error_log.txt"
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

:: Function to build Docker image
:buildDockerImage
echo Building Docker image...
REM Add the command to build the Docker image
REM For example:
docker build -t myapp:latest .
call :checkError "Docker Image Build"
goto :eof

:: Function to run Docker container
:runDockerContainer
echo Running Docker container...
REM Add the command to run the Docker container
REM For example:
docker run -d -p 80:80 --name myapp_container myapp:latest
call :checkError "Docker Container Run"
goto :eof

:: Function to stop Docker container
:stopDockerContainer
echo Stopping Docker container...
REM Add the command to stop the Docker container
REM For example:
docker stop myapp_container
call :checkError "Docker Container Stop"
goto :eof

:: Function to remove Docker container
:removeDockerContainer
echo Removing Docker container...
REM Add the command to remove the Docker container
REM For example:
docker rm myapp_container
call :checkError "Docker Container Remove"
goto :eof

:: Function to manage Docker volumes (Optional)
:manageDockerVolumes
echo Managing Docker volumes...
REM Add commands to manage Docker volumes
REM For example, to create a volume:
REM docker volume create myapp_data
REM To remove a volume:
REM docker volume rm myapp_data
goto :eof

:: Function to manage Docker networks (Optional)
:manageDockerNetworks
echo Managing Docker networks...
REM Add commands to manage Docker networks
REM For example, to create a network:
REM docker network create myapp_network
REM To remove a network:
REM docker network rm myapp_network
goto :eof

:: Function to log Docker steps
:logDockerStep
echo Logging Docker step: %1
echo %DATE% %TIME% - %1 >> docker_log.txt
goto :eof

:: Ensure the script runs with administrative privileges
call :ensureAdmin

:: Install Docker if not already installed
call :installDocker

:: Start Docker service
call :startDocker

:: Check Docker daemon status
call :checkDockerDaemon

:: Log Docker step
call :logDockerStep "Build Docker Image"

:: Build Docker image
call :buildDockerImage

:: Log Docker step
call :logDockerStep "Run Docker Container"

:: Run Docker container
call :runDockerContainer

:: Log Docker step
call :logDockerStep "Manage Docker Volumes"

:: Manage Docker volumes (Optional)
call :manageDockerVolumes

:: Log Docker step
call :logDockerStep "Manage Docker Networks"

:: Manage Docker networks (Optional)
call :manageDockerNetworks

:: Log Docker step
call :logDockerStep "Stop Docker Container"

:: Stop Docker container (Optional)
call :stopDockerContainer

:: Log Docker step
call :logDockerStep "Remove Docker Container"

:: Remove Docker container (Optional)
call :removeDockerContainer

echo [****| Docker container management complete! |****]
echo Logs can be found in "%~dp0docker_error_log.txt"
pause
exit /b 0

endlocal