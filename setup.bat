@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM Project Zomboid Server Manager - Automated Setup & Installer
REM ============================================================

echo.
echo ============================================================
echo   Project Zomboid Server Manager - Quick Setup (Windows)
echo ============================================================
echo.

REM 1. Check Python installation and version (3.8+)
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Please install Python 3.8 or higher from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [1/4] Found Python version: %PY_VER%

REM Verify version is >= 3.8 using Python one-liner
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.8 or higher is required. Found: %PY_VER%
    pause
    exit /b 1
)

REM 2. Create virtual environment if it does not exist
if not exist "venv" (
    echo [2/4] Creating virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [2/4] Virtual environment already exists.
)

REM 3. Activate venv and install requirements
echo [3/4] Installing dependencies from requirements.txt...
call venv\Scripts\activate.bat
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies failed to install. Retrying with default pip...
    pip install -r requirements.txt
)

REM 4. Create Desktop Shortcut pointing to run.bat
echo [4/4] Creating Desktop Shortcut...
set SCRIPT_DIR=%~dp0
set RUN_BAT=%SCRIPT_DIR%run.bat
set SHORTCUT=%USERPROFILE%\Desktop\PZ Server Manager.lnk

powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%'); $s.TargetPath='%RUN_BAT%'; $s.WorkingDirectory='%SCRIPT_DIR%'; $s.WindowStyle=1; $s.Description='Project Zomboid Server Manager'; $s.Save()"

echo.
echo ============================================================
echo   Setup Completed Successfully!
echo ============================================================
echo   A shortcut "PZ Server Manager" has been created on your Desktop.
echo   You can now double-click the shortcut or run run.bat to launch.
echo.
pause
