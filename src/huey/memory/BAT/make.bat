@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
call "%SCRIPT_DIR%_common.bat" :resolve_repo_root ROOT_DIR "%SCRIPT_DIR%"
if errorlevel 1 (
    echo [ERROR] Could not locate the repository root from "%SCRIPT_DIR%".
    exit /b 1
)

call "%SCRIPT_DIR%_common.bat" :resolve_python "%ROOT_DIR%" PYTHON_EXE
if errorlevel 1 (
    echo [ERROR] Python was not found.
    exit /b 1
)

set "DOCS_DIR=%ROOT_DIR%\docs"
set "BUILD_DIR=%DOCS_DIR%\_build"
set "TARGET=%~1"
if not defined TARGET set "TARGET=help"

if not exist "%DOCS_DIR%\conf.py" (
    echo [ERROR] Sphinx configuration not found at "%DOCS_DIR%\conf.py".
    exit /b 1
)

"%PYTHON_EXE%" -c "import sphinx" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Sphinx is not installed in the active Python environment.
    echo         Install docs\requirements.txt or your full project dependencies first.
    exit /b 1
)

pushd "%DOCS_DIR%" >nul
"%PYTHON_EXE%" -m sphinx -M %TARGET% "%DOCS_DIR%" "%BUILD_DIR%" %SPHINXOPTS% %O%
set "EXIT_CODE=%errorlevel%"
popd >nul

exit /b %EXIT_CODE%
