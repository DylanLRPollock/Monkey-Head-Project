REM Monkey Head Project
REM By: Dylan L.R. Pollock
REM www.dlrp.ca
REM HueyOS: Windows Remove Tool batch script (setup/Windows10)

# ==================================================  #
# This file is a part of the 'Monkey Head Project'                                       #
# Website:   https://dlrp.ca                                                                            #
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project    #
# License:   https://opensource.org/license/gpl-3-0                                 #
# Overseen By:   Dylan L.R. Pollock                                                             #
# Updated: 06.07.2025                                                                                 #
# ================================================== #
:: START OF Lightweight_Windows10_Optimization.bat
:: Lightweight Windows 10 Optimization Script
:: Removes unnecessary programs, settings, and files for a slimmer OS experience.
@echo off

:: Ensure the script is run as Administrator
if not "%~1"=="admin" (
    powershell -Command "Start-Process '%~f0' -ArgumentList 'admin' -Verb RunAs"
    exit /b
)

:: Disable unnecessary services
echo Disabling unnecessary services...
powershell -Command "Get-Service | Where-Object { $_.Status -eq 'Running' -and $_.CanStop -eq $true -and ($_.DisplayName -notmatch '(Windows Update|Audio|Network)') } | Stop-Service"

:: Remove unnecessary default Windows apps
echo Removing unnecessary default Windows apps...
powershell -Command "Get-AppxPackage | Where-Object { $_.Name -notmatch '(WindowsStore|Xbox|Photos)' } | Remove-AppxPackage"

:: Clean temporary files
echo Cleaning temporary files...
del /q /s %TEMP%\\*
rd /s /q %TEMP%\\
echo Temp files cleaned.

:: Disable visual effects for performance
echo Disabling visual effects for performance...
powershell -Command "Set-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects' -Name 'VisualFXSetting' -Value 2"

:: Remove unnecessary startup items
echo Removing unnecessary startup items...
powershell -Command "Get-CimInstance Win32_StartupCommand | Remove-CimInstance"

:: Optimize the power plan for high performance
echo Setting high-performance power plan...
powercfg /SETACTIVE SCHEME_MIN

:: Disable telemetry and tracking
echo Disabling telemetry and tracking...
powershell -Command "Stop-Service diagtrack"
powershell -Command "Set-Service diagtrack -StartupType Disabled"

:: Final Summary
echo Optimization complete! Your system is now lighter and faster.
pause
exit

:: END OF Lightweight_Windows10_Optimization.bat

:: START OF Lightweight_Windows11_Optimization.bat

:: Lightweight Windows 11 Optimization Script
:: Removes unnecessary programs, settings, and files for a slimmer OS experience.
@echo off

:: Run as Administrator
if not "%~1"=="admin" (powershell -Command "Start-Process '%~f0' -ArgumentList 'admin' -Verb RunAs" & exit /b)

:: Disable unnecessary services
echo Disabling unnecessary services...
powershell -Command "Get-Service | Where-Object { $_.Status -eq 'Running' -and $_.CanStop -eq $true -and ($_.DisplayName -notmatch '(Windows Update|Audio|Network)') } | Stop-Service"

:: Remove default Windows apps
echo Removing default Windows apps...
powershell -Command "Get-AppxPackage | Where-Object { $_.Name -notmatch '(Microsoft.Store|Xbox|Photos)' } | Remove-AppxPackage"

:: Clean temporary files
echo Cleaning temporary files...
del /q /s %TEMP%\*
rd /s /q %TEMP%\
echo Temp files cleaned.

:: Disable visual effects for performance
echo Disabling visual effects for performance...
powershell -Command "Set-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects' -Name 'VisualFXSetting' -Value 2"

:: Remove unnecessary startup items
echo Removing unnecessary startup items...
powershell -Command "Get-CimInstance Win32_StartupCommand | Remove-CimInstance"

:: Optimize power plan
echo Setting high-performance power plan...
powercfg -SETACTIVE SCHEME_MIN

:: Disable telemetry and tracking
echo Disabling telemetry and tracking...
powershell -Command "Stop-Service diagtrack"
powershell -Command "Set-Service diagtrack -StartupType Disabled"

:: Summary
echo Optimization complete! Your system is now lighter and faster.
pause
exit

:: END OF Lightweight_Windows11_Optimization.bat

:: START OF windows-remove-tool.bat
@echo off
setlocal

REM Define log file
set logfile=%~dp0cleanup_log.txt
if exist %logfile% del %logfile%
echo Cleanup script started on %date% at %time% >> %logfile%

REM Check if the system is Windows 10 or Windows 11
ver | findstr /i "10\.0\.19041 10\.0\.22000 10\.0\.22621" >nul
if %errorlevel%==0 (
    echo Running on Windows 10 or Windows 11...
    echo Running on Windows 10 or Windows 11... >> %logfile%
) else (
    echo This script only supports Windows 10 or Windows 11.
    echo Unsupported Windows version detected. Exiting... >> %logfile%
    exit /b
)

REM Function to log errors
:log_error
echo ERROR: %~1 failed at %date% %time% >> %logfile%
goto :eof

REM User prompt to continue with cleanup
echo WARNING: This script will perform significant cleanup, including removing services and files.
choice /m "Do you wish to continue?"
if %errorlevel% neq 1 (
    echo User chose to exit the script. >> %logfile%
    exit /b
)

REM Remove Remote Desktop Services and Assistance
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Remote Assistance" /v "fAllowToGetHelp" /t REG_DWORD /d 0 /f || call :log_error "Disable Remote Assistance"
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Terminal Server" /v "fDenyTSConnections" /t REG_DWORD /d 1 /f || call :log_error "Disable Terminal Services"

REM Disable Event Logging (if not needed)
sc query "eventlog" >nul 2>&1 && (
    sc stop "eventlog" || call :log_error "Stop Event Log"
    sc config "eventlog" start= disabled || call :log_error "Disable Event Log Startup"
)

REM Disable Connected Devices Platform Service
sc query "CDPUserSvc" >nul 2>&1 && (
    sc stop "CDPUserSvc" || call :log_error "Stop CDPUserSvc"
    sc config "CDPUserSvc" start= disabled || call :log_error "Disable CDPUserSvc Startup"
)

REM Disable Diagnostic Tracking Service (telemetry)
sc query "DiagTrack" >nul 2>&1 && (
    sc stop "DiagTrack" || call :log_error "Stop DiagTrack"
    sc config "DiagTrack" start= disabled || call :log_error "Disable DiagTrack Startup"
)

REM Disable Superfetch (if using SSDs)
sc query "SysMain" >nul 2>&1 && (
    sc stop "SysMain" || call :log_error "Stop SysMain"
    sc config "SysMain" start= disabled || call :log_error "Disable SysMain Startup"
)

REM Disable Windows Update (manage updates manually)
sc query "wuauserv" >nul 2>&1 && (
    sc stop "wuauserv" || call :log_error "Stop Windows Update Service"
    sc config "wuauserv" start= disabled || call :log_error "Disable Windows Update Startup"
)

REM Remove unnecessary system folders with confirmation
echo Deleting old driver files (DriverStore\FileRepository)...
if exist "%systemroot%\System32\DriverStore\FileRepository" rd /s /q "%systemroot%\System32\DriverStore\FileRepository" || call :log_error "Remove DriverStore\FileRepository"

REM Unused installers (be careful, some rollback installers may be needed)
echo Deleting unused installers...
if exist "%systemroot%\Installer" rd /s /q "%systemroot%\Installer" || call :log_error "Remove Installer Directory"

REM Windows Defender folder (if using third-party antivirus)
echo Deleting Windows Defender files...
if exist "C:\ProgramData\Microsoft\Windows Defender" rd /s /q "C:\ProgramData\Microsoft\Windows Defender" || call :log_error "Remove Windows Defender Directory"

REM Clean temporary files and recycle bin
echo Cleaning temporary files...
if exist "%temp%" rd /s /q "%temp%" || call :log_error "Remove Temp Folder"
del /f /s /q "%systemroot%\Temp\*" || call :log_error "Delete System Temp Files"
del /f /s /q "%systemroot%\Prefetch\*" || call :log_error "Delete Prefetch Files"
powershell -command "Clear-RecycleBin -Force" || call :log_error "Clear Recycle Bin"

REM Disable Speech recognition, Cortana, and unnecessary voice services
echo Disabling Speech and Cortana services...
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Speech" /v "AllowSpeechPlatformDataCollection" /t REG_DWORD /d 0 /f || call :log_error "Disable Speech Data Collection"
powershell -command "Get-AppxPackage *cortana* | Remove-AppxPackage" || call :log_error "Remove Cortana"
sc query "SpeechRuntime" >nul 2>&1 && (
    sc stop "SpeechRuntime" || call :log_error "Stop SpeechRuntime"
    sc config "SpeechRuntime" start= disabled || call :log_error "Disable SpeechRuntime Startup"
)

REM Remove Windows Media Player
dism /online /Disable-Feature /FeatureName:WindowsMediaPlayer /NoRestart || call :log_error "Remove Windows Media Player"

REM Remove unnecessary optional features (example: TIFF iFilter, XPS Viewer)
dism /online /Disable-Feature /FeatureName:Printing-XPSServices-Features /NoRestart || call :log_error "Disable XPS Viewer"
dism /online /Disable-Feature /FeatureName:SearchEngine-Filter-TIFFIFilter /NoRestart || call :log_error "Disable TIFF iFilter"

REM Disable more telemetry-related scheduled tasks
echo Disabling telemetry-related scheduled tasks...
schtasks /Query /TN "\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser" >nul 2>&1 && (
    schtasks /Change /TN "\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser" /Disable || call :log_error "Disable Microsoft Compatibility Appraiser"
)
schtasks /Query /TN "\Microsoft\Windows\Autochk\Proxy" >nul 2>&1 && (
    schtasks /Change /TN "\Microsoft\Windows\Autochk\Proxy" /Disable || call :log_error "Disable Autochk Proxy"
)
schtasks /Query /TN "\Microsoft\Windows\Customer Experience Improvement Program\Consolidator" >nul 2>&1 && (
    schtasks /Change /TN "\Microsoft\Windows\Customer Experience Improvement Program\Consolidator" /Disable || call :log_error "Disable Consolidator"
)
schtasks /Query /TN "\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip" >nul 2>&1 && (
    schtasks /Change /TN "\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip" /Disable || call :log_error "Disable UsbCeip"
)
schtasks /Query /TN "\Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector" >nul 2>&1 && (
    schtasks /Change /TN "\Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector" /Disable || call :log_error "Disable Disk Diagnostic Data Collector"
)

REM Remove Delivery Optimization files and services (if not using peer-to-peer updates)
sc query "DoSvc" >nul 2>&1 && (
    sc stop "DoSvc" || call :log_error "Stop Delivery Optimization Service"
    sc config "DoSvc" start= disabled || call :log_error "Disable Delivery Optimization Service"
)
if exist "%systemroot%\SoftwareDistribution\DeliveryOptimization" rd /s /q "%systemroot%\SoftwareDistribution\DeliveryOptimization" || call :log_error "Remove Delivery Optimization Files"

REM Remove Windows.old (previous Windows installations)
if exist "%systemroot%\Windows.old" rd /s /q "%systemroot%\Windows.old" || call :log_error "Remove Windows.old"

REM Final cleanup
echo Cleanup completed successfully on %date% at %time% >> %logfile%
echo Cleanup completed successfully. Log saved to %logfile%.
endlocal

:: END OF windows-remove-tool.bat
