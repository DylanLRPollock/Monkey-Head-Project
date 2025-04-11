@echo off
setlocal enabledelayedexpansion

:: Change to the script's own directory
cd /d "%~dp0"

:: Clear screen and set color
cls
color 0A
echo [****|     09_KUBERNETES.bat - Kubernetes Management   |****]
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
echo %date% %time% - Error: %1 failed with error code %errorlevel% >> "%~dp0kubernetes_error_log.txt"
goto :eof

:: Function to install Kubernetes tools if not already installed
:installK8sTools
echo Checking for kubectl and Minikube installation...
kubectl version --client >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing kubectl...
    choco install -y kubernetes-cli
    call :checkError "kubectl Installation"
) else (
    echo kubectl is already installed.
)

minikube version >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Minikube...
    choco install -y minikube
    call :checkError "Minikube Installation"
) else (
    echo Minikube is already installed.
)
goto :eof

:: Function to start Minikube
:startMinikube
echo Starting Minikube...
minikube start
call :checkError "Starting Minikube"
goto :eof

:: Function to stop Minikube
:stopMinikube
echo Stopping Minikube...
minikube stop
call :checkError "Stopping Minikube"
goto :eof

:: Function to check Minikube status
:checkMinikubeStatus
echo Checking Minikube status...
minikube status >nul 2>&1
if %errorlevel% neq 0 (
    echo Minikube is not running.
    call :startMinikube
) else (
    echo Minikube is running.
)
goto :eof

:: Function to deploy application to Kubernetes
:deployApp
echo Deploying application to Kubernetes...
REM Add the command to apply Kubernetes configurations
REM For example:
kubectl apply -f k8s/
call :checkError "Deploying Application to Kubernetes"
goto :eof

:: Function to get status of Kubernetes resources
:getStatus
echo Getting status of Kubernetes resources...
kubectl get all --namespace=default
call :checkError "Getting Kubernetes Resource Status"
goto :eof

:: Function to delete Kubernetes resources
:deleteResources
echo Deleting Kubernetes resources...
kubectl delete -f k8s/
call :checkError "Deleting Kubernetes Resources"
goto :eof

:: Function to describe Kubernetes pod for debugging
:describePod
set /p podName="Enter the name of the pod to describe: "
if "%podName%"=="" (
    echo Pod name cannot be empty.
    pause
    exit /b 1
)
echo Describing pod %podName%...
kubectl describe pod %podName%
call :checkError "Describing Kubernetes Pod"
goto :eof

:: Function to get logs of a Kubernetes pod for debugging
:getPodLogs
set /p podName="Enter the name of the pod to get logs: "
if "%podName%"=="" (
    echo Pod name cannot be empty.
    pause
    exit /b 1
)
echo Getting logs for pod %podName%...
kubectl logs %podName%
call :checkError "Getting Kubernetes Pod Logs"
goto :eof

:: Function to log Kubernetes management steps
:logK8sStep
echo Logging Kubernetes management step: %1
echo %DATE% %TIME% - %1 >> kubernetes_log.txt
goto :eof

:: Ensure the script runs with administrative privileges
call :ensureAdmin

:: Install Kubernetes tools if not already installed
call :installK8sTools

:menu
cls
echo [****|     Kubernetes Management   |****]
echo [1] Start Minikube
echo [2] Stop Minikube
echo [3] Check Minikube Status
echo [4] Deploy Application to Kubernetes
echo [5] Get Status of Kubernetes Resources
echo [6] Delete Kubernetes Resources
echo [7] Describe a Kubernetes Pod
echo [8] Get Logs of a Kubernetes Pod
echo [E] Exit
echo.
set /p action="Please select an option (1-8, E to exit): "
if "%action%"=="1" goto startMinikube
if "%action%"=="2" goto stopMinikube
if "%action%"=="3" goto checkMinikubeStatus
if "%action%"=="4" goto deployApp
if "%action%"=="5" goto getStatus
if "%action%"=="6" goto deleteResources
if "%action%"=="7" goto describePod
if "%action%"=="8" goto getPodLogs
if /i "%action%"=="E" goto end
echo Invalid selection, please try again.
pause
goto menu

:end
echo [****| Kubernetes management complete! |****]
pause
exit /b 0

endlocal