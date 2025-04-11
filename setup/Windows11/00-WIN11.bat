@echo off
setlocal enabledelayedexpansion

:: Change to the script's own directory
cd /d "%~dp0"

:: Clear screen and set color
cls
color 0A
echo [****|    00 - WIN10.bat - GenCore AI/OS - Windows 11 Pro For Workstations x64   |****]
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
REM Check for Windows version
ver | find "10" >nul
call :checkError "Windows 11 Check"
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

:: Function to clone the repository
:cloneRepository
echo Cloning repository...
if not exist "%USERPROFILE%\Source" mkdir "%USERPROFILE%\Source"
cd "%USERPROFILE%\Source"
git clone https://github.com/your/repo.git
call :checkError "Git Clone"
goto :eof

:: Function to set up Python environment
:setupPythonEnv
echo Setting up Python environment...
cd "%USERPROFILE%\Source\repo"
python -m venv venv
call :checkError "Python Virtual Environment Setup"
venv\Scripts\activate
call :checkError "Activate Python Virtual Environment"
pip install -r requirements.txt
call :checkError "Install Python Requirements"
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

:: Function to update Python packages
:update_python_packages
echo Updating Python Packages...
pip install --upgrade pip
call :checkError "Pip Upgrade"
pip install --upgrade -r requirements.txt
call :checkError "Update Python Packages"
goto :eof

:: Function to build the system
:build_system
echo Building System...
REM Add commands to build the system here
REM Example:
cd "%USERPROFILE%\Source\repo"
python setup.py build
call :checkError "Build System"
goto :eof

:: Function to manage Docker containers
:manage_containers
echo Managing Containers...
REM Add commands to manage Docker containers here
REM Example:
docker-compose up -d
call :checkError "Start Docker Containers"
docker ps
call :checkError "List Running Containers"
goto :eof

:: Function to manage Docker volumes
:manage_volumes
echo Managing Volumes...
REM Add commands to manage Docker volumes here
REM Example:
docker volume ls
call :checkError "List Docker Volumes"
docker volume prune -f
call :checkError "Prune Docker Volumes"
goto :eof

:: Function to deploy with Kubernetes
:deploy_kubernetes
echo Deploying with Kubernetes...
REM Add commands to deploy with Kubernetes here
REM Example:
kubectl apply -f deployment.yaml
call :checkError "Deploy Kubernetes Resources"
kubectl get pods
call :checkError "Get Kubernetes Pods"
goto :eof

:: Function to start the system
:start_system
echo Starting System...
REM Add commands to start the system here
REM Example:
cd "%USERPROFILE%\Source\repo"
python main.py
call :checkError "Start System"
goto :eof

:: Function to set up HostOS
:setup_hostos
echo Setting up HostOS...
REM Add commands to set up HostOS here
REM Example:
choco install -y htop
call :checkError "Install htop"
goto :eof

:: Function to set up SubOS
:setup_subos
echo Setting up SubOS...
REM Add commands to set up SubOS here
REM Example:
REM Placeholder for SubOS setup commands
call :checkError "Setup SubOS"
goto :eof

:: Function to set up NanoOS
:setup_nanoos
echo Setting up NanoOS...
REM Add commands to set up NanoOS here
REM Example:
REM Placeholder for NanoOS setup commands
call :checkError "Setup NanoOS"
goto :eof

:: Function to manage Kubernetes
:kubernetes_management
echo Managing Kubernetes...
REM Add commands to manage Kubernetes here
REM Example:
kubectl get nodes
call :checkError "Get Kubernetes Nodes"
kubectl get services
call :checkError "Get Kubernetes Services"
goto :eof

:: Function to check system status
:status
echo Checking System Status...
REM Call a status script or include status commands here
echo Checking Docker status...
docker ps
call :checkError "Check Docker Status"
echo Checking Kubernetes status...
kubectl get pods
call :checkError "Check Kubernetes Status"
goto :eof

:: Function to backup configurations
:backup_config
echo Backing up Configurations...
REM Placeholder for backup commands
REM Example:
xcopy /E /I /Y %USERPROFILE%\Source\repo\config %USERPROFILE%\Backup\repo\config
call :checkError "Backup Configurations"
goto :eof

:: Function to restore configurations
:restore_config
echo Restoring Configurations...
REM Placeholder for restore commands
REM Example:
xcopy /E /I /Y %USERPROFILE%\Backup\repo\config %USERPROFILE%\Source\repo\config
call :checkError "Restore Configurations"
goto :eof

:: Function to check and install dependencies
:check_dependencies
echo Checking and Installing Dependencies...
REM Placeholder for dependency checks and installations
REM Example:
powershell -command "Get-Command terraform -ErrorAction SilentlyContinue" >nul
if %errorlevel% neq 0 (
    choco install -y terraform
    call :checkError "Install Terraform"
)
goto :eof

:: Function to launch terminal
:launch_terminal
echo Launching Terminal...
call :ensureAdmin
start powershell
call :checkError "Launch Terminal"
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

echo Installing optional tools...
call :installOptionalTools

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

:menu
cls
echo.
echo Main Menu:
echo.
echo 1. Full Setup
echo 2. Mini Setup
echo 3. Cleanup
echo 4. Launch Terminal
echo 5. Update Python Packages
echo 6. Build System
echo 7. Manage Containers
echo 8. Manage Volumes
echo 9. Deploy with Kubernetes
echo 10. Start System
echo 11. Setup HostOS
echo 12. Setup SubOS
echo 13. Setup NanoOS
echo 14. Kubernetes Management
echo 15. Check System Status
echo 16. Backup Configurations
echo 17. Restore Configurations
echo 18. Check Dependencies
echo E. Exit
echo.
set /p choice=Enter your choice: 
if /i "%choice%"=="1" goto full_setup
if /i "%choice%"=="2" goto mini_setup
if /i "%choice%"=="3" goto cleanup
if /i "%choice%"=="4" goto launch_terminal
if /i "%choice%"=="5" goto update_python_packages
if /i "%choice%"=="6" goto build_system
if /i "%choice%"=="7" goto manage_containers
if /i "%choice%"=="8" goto manage_volumes
if /i "%choice%"=="9" goto deploy_kubernetes
if /i "%choice%"=="10" goto start_system
if /i "%choice%"=="11" goto setup_hostos
if /i "%choice%"=="12" goto setup_subos
if /i "%choice%"=="13" goto setup_nanoos
if /i "%choice%"=="14" goto kubernetes_management
if /i "%choice%"=="15" goto status
if /i "%choice%"=="16" goto backup_config
if /i "%choice%"=="17" goto restore_config
if /i "%choice%"=="18" goto check_dependencies
if /i "%choice%"=="E" goto end
goto menu

:full_setup
echo [****| Full Setup |****]
call :ensureAdmin
call :systemCheck
call :installChocolatey
call :installCommonTools
call :installAdditionalTools
call 02_FULL.bat
call :checkError "Full Setup"
goto menu

:mini_setup
echo [****| Mini Setup |****]
call :ensureAdmin
call :systemCheck
call :installChocolatey
call :installCommonTools
call :installAdditionalTools
call 02_MINI.bat
call :checkError "Mini Setup"
goto menu

:cleanup
echo [****| Cleanup |****]
call :ensureAdmin
call 03_CLEANUP.bat
call :checkError "Cleanup Files"
goto menu

:launch_terminal
echo [****| Launching Terminal |****]
call :ensureAdmin
call 04_TERMINAL.bat
call :checkError "Launch Terminal"
goto menu

:update_python_packages
echo [****| Updating Python Packages |****]
call :ensureAdmin
call 05_UPDATE.bat
call :checkError "Update Python Packages"
goto menu

:build_system
echo [****| Building System |****]
call :ensureAdmin
call 06_BUILD.bat
call :checkError "Build System"
goto menu

:manage_containers
echo [****| Managing Containers |****]
call :ensureAdmin
call 07_CONTAINER.bat
call :checkError "Manage Containers"
goto menu

:manage_volumes
echo [****| Managing Volumes |****]
call :ensureAdmin
call 08_VOLUME.bat
call :checkError "Manage Volumes"
goto menu

:deploy_kubernetes
echo [****| Deploying with Kubernetes |****]
call :ensureAdmin
call 09_KUBERNETES.bat
call :checkError "Deploy Kubernetes"
goto menu

:start_system
echo [****| Starting System |****]
call :ensureAdmin
call 10_START.bat
call :checkError "Start System"
goto menu

:setup_hostos
echo [****| Setting up HostOS |****]
call :ensureAdmin
call 11_HOSTOS.bat
call :checkError "Setup HostOS"
goto menu

:setup_subos
echo [****| Setting up SubOS |****]
call :ensureAdmin
call 12_SUBOS.bat
call :checkError "Setup SubOS"
goto menu

:setup_nanoos
echo [****| Setting up NanoOS |****]
call :ensureAdmin
call 13_NANOOS.bat
call :checkError "Setup NanoOS"
goto menu

:kubernetes_management
echo [****| Kubernetes Management |****]
call :ensureAdmin
call 14_KUBERNETES_MANAGE.bat
call :checkError "Kubernetes Management"
goto menu

:status
echo [****| Checking System Status |****]
call :ensureAdmin
REM Call a status script or include status commands here
echo Checking Docker status...
docker ps
call :checkError "Check Docker Status"
echo Checking Kubernetes status...
kubectl get pods
call :checkError "Check Kubernetes Status"
goto menu

:backup_config
echo [****| Backing up Configurations |****]
REM Placeholder for backup commands
REM Example:
xcopy /E /I /Y %USERPROFILE%\Source\repo\config %USERPROFILE%\Backup\repo\config
call :checkError "Backup Configurations"
goto menu

:restore_config
echo [****| Restoring Configurations |****]
REM Placeholder for restore commands
REM Example:
xcopy /E /I /Y %USERPROFILE%\Backup\repo\config %USERPROFILE%\Source\repo\config
call :checkError "Restore Configurations"
goto menu

:check_dependencies
echo [****| Checking and Installing Dependencies |****]
REM Placeholder for dependency checks and installations
REM Example:
powershell -command "Get-Command terraform -ErrorAction SilentlyContinue" >nul
if %errorlevel% neq 0 (
    choco install -y terraform
    call :checkError "Install Terraform"
)
goto :eof

:end
echo [****| Exiting WIN10.bat. Thank you for using GenCore. |****]
pause
exit /b

endlocal