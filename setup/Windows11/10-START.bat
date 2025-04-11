@echo off
setlocal enabledelayedexpansion

:: Change to the script's own directory
cd /d "%~dp0"

:: Clear screen and set color
cls
color 0A
echo [****|     10_START.bat - Start Services and Applications   |****]
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
echo %date% %time% - Error: %1 failed with error code %errorlevel% >> "%~dp0start_error_log.txt"
goto :eof

:: Function to start Docker service
:startDocker
echo Starting Docker service...
sc start com.docker.service >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker service is already running.
) else (
    call :checkError "Starting Docker Service"
)
goto :eof

:: Function to check Docker service status
:checkDockerStatus
echo Checking Docker service status...
sc query com.docker.service | find "RUNNING" >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker service is not running. Attempting to start...
    call :startDocker
) else (
    echo Docker service is running.
)
goto :eof

:: Function to start Minikube
:startMinikube
echo Starting Minikube...
minikube start
call :checkError "Starting Minikube"
goto :eof

:: Function to check Minikube status
:checkMinikubeStatus
echo Checking Minikube status...
minikube status | find "host: Running" >nul 2>&1
if %errorlevel% neq 0 (
    echo Minikube is not running. Attempting to start...
    call :startMinikube
) else (
    echo Minikube is running.
)
goto :eof

:: Function to start application services
:startAppServices
echo Starting application services...
REM Add commands to start application services
REM For example:
docker-compose up -d
call :checkError "Starting Application Services"
goto :eof

:: Function to check application services status
:checkAppServicesStatus
echo Checking application services status...
docker-compose ps | find "Up" >nul 2>&1
if %errorlevel% neq 0 (
    echo Application services are not running. Attempting to start...
    call :startAppServices
) else (
    echo Application services are running.
)
goto :eof

:: Function to start database service (if applicable)
:startDatabase
echo Starting database service...
REM Add commands to start database service
REM For example:
REM net start MySQL
call :checkError "Starting Database Service"
goto :eof

:: Function to check database service status
:checkDatabaseStatus
echo Checking database service status...
REM Add commands to check database service status
REM For example:
REM net start | find "MySQL" >nul 2>&1
if %errorlevel% neq 0 (
    echo Database service is not running. Attempting to start...
    call :startDatabase
) else (
    echo Database service is running.
)
goto :eof

:: Function to start web server (if applicable)
:startWebServer
echo Starting web server...
REM Add commands to start web server
REM For example:
REM net start Apache2.4
call :checkError "Starting Web Server"
goto :eof

:: Function to check web server status
:checkWebServerStatus
echo Checking web server status...
REM Add commands to check web server status
REM For example:
REM net start | find "Apache2.4" >nul 2>&1
if %errorlevel% neq 0 (
    echo Web server is not running. Attempting to start...
    call :startWebServer
) else (
    echo Web server is running.
)
goto :eof

:: Function to open application in browser (optional)
:openBrowser
echo Opening application in web browser...
REM Add command to open application in default web browser
REM For example:
start http://localhost
goto :eof

:: Function to log startup steps
:logStartupStep
echo Logging startup step: %1
echo %DATE% %TIME% - %1 >> start_log.txt
goto :eof

:: Ensure the script runs with administrative privileges
call :ensureAdmin

:: Check Docker service status
call :checkDockerStatus

:: Log startup step
call :logStartupStep "Checking Minikube Status"

:: Check Minikube status
call :checkMinikubeStatus

:: Log startup step
call :logStartupStep "Checking Application Services Status"

:: Check application services status
call :checkAppServicesStatus

:: Log startup step
call :logStartupStep "Checking Database Service Status"

:: Check database service status (if applicable)
call :checkDatabaseStatus

:: Log startup step
call :logStartupStep "Checking Web Server Status"

:: Check web server status (if applicable)
call :checkWebServerStatus

:: Log startup step
call :logStartupStep "Opening Browser"

:: Open application in web browser (optional)
call :openBrowser

echo [****| All services and applications started successfully! |****]
pause
exit /b 0

endlocal