@echo off
where git >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Git is already available on PATH.
    exit /b 0
)

where winget >nul 2>&1
if errorlevel 1 (
    echo [ERROR] winget is not available. Install App Installer or Git manually.
    exit /b 1
)

winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
exit /b %errorlevel%
