@echo off
setlocal enabledelayedexpansion

:: Change to the script's own directory
cd /d "%~dp0"

:: Clear screen and set color
cls
color 0A
echo [****|     E_EXIT.bat - Shutdown and Cleanup   |****]
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
echo %date% %time% - Error: %1 failed with error code %errorlevel% >> "%~dp0exit_error_log.txt"
goto :eof

:: Function to stop Docker containers
:stopDockerContainers
echo Stopping Docker containers...
for /f "tokens=*" %%i in ('docker ps -q') do (
    docker stop %%i >nul 2>&1
    call :checkError "Stopping Docker Container %%i"
)
goto :eof

:: Function to remove Docker containers
:removeDockerContainers
echo Removing Docker containers...
for /f "tokens=*" %%i in ('docker ps -a -q') do (
    docker rm %%i >nul 2>&1
    call :checkError "Removing Docker Container %%i"
)
goto :eof

:: Function to stop Minikube
:stopMinikube
echo Stopping Minikube...
minikube status | find "host: Running" >nul 2>&1
if %errorlevel% neq 0 (
    echo Minikube is not running.
) else (
    minikube stop >nul 2>&1
    call :checkError "Stopping Minikube"
)
goto :eof

:: Function to stop application services
:stopAppServices
echo Stopping application services...
docker-compose ps >nul 2>&1
if %errorlevel% neq 0 (
    echo No application services to stop.
) else (
    docker-compose down >nul 2>&1
    call :checkError "Stopping Application Services"
)
goto :eof

:: Function to stop database service (if applicable)
:stopDatabaseService
echo Stopping database service...
REM Add commands to check and stop database service
REM For example:
REM sc query MySQL | find "RUNNING" >nul 2>&1
REM if %errorlevel% neq 0 (
REM     echo MySQL service is not running.
REM ) else (
REM     net stop MySQL
REM     call :checkError "Stopping MySQL Service"
REM )
goto :eof

:: Function to stop web server (if applicable)
:stopWebServer
echo Stopping web server...
REM Add commands to check and stop web server
REM For example:
REM sc query Apache2.4 | find "RUNNING" >nul 2>&1
REM if %errorlevel% neq 0 (
REM     echo Apache2.4 web server is not running.
REM ) else (
REM     net stop Apache2.4
REM     call :checkError "Stopping Apache2.4 Web Server"
REM )
goto :eof

:: Function to clean up temporary files
:cleanupTempFiles
echo Cleaning up temporary files...
del /F /Q %TEMP%\* >nul 2>&1
call :checkError "Cleaning Up Temporary Files"
goto :eof

:: Function to log shutdown steps
:logShutdownStep
echo Logging shutdown step: %1
echo %DATE% %TIME% - %1 >> "%~dp0exit_log.txt"
goto :eof

:: Ensure the script runs with administrative privileges
call :ensureAdmin

:: Log shutdown step
call :logShutdownStep "Stopping Docker Containers"

:: Stop Docker containers
call :stopDockerContainers

:: Log shutdown step
call :logShutdownStep "Removing Docker Containers"

:: Remove Docker containers
call :removeDockerContainers

:: Log shutdown step
call :logShutdownStep "Stopping Minikube"

:: Stop Minikube
call :stopMinikube

:: Log shutdown step
call :logShutdownStep "Stopping Application Services"

:: Stop application services
call :stopAppServices

:: Log shutdown step
call :logShutdownStep "Stopping Database Service"

:: Stop database service (if applicable)
call :stopDatabaseService

:: Log shutdown step
call :logShutdownStep "Stopping Web Server"

:: Stop web server (if applicable)
call :stopWebServer

:: Log shutdown step
call :logShutdownStep "Cleaning Up Temporary Files"

:: Clean up temporary files
call :cleanupTempFiles

echo [****| Shutdown and cleanup complete! |****]
pause
exit /b 0

endlocal
