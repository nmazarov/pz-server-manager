@echo off
REM ============================================
REM PZ Server Manager - Build Script for Windows
REM ============================================

echo.
echo ========================================
echo   PZ Server Manager - Build Script
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [1/4] Checking Python version...
python --version

REM Create virtual environment if not exists
if not exist "venv" (
    echo [2/4] Creating virtual environment...
    python -m venv venv
) else (
    echo [2/4] Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo [3/4] Installing dependencies...
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

REM Build executable
echo [4/4] Building executable...
echo.

pyinstaller --clean --noconfirm pz_server_manager.spec

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build Complete!
echo ========================================
echo.
echo Executable location:
echo   dist\PZ Server Manager.exe
echo.
echo You can now copy this file anywhere and run it.
echo.

REM Deactivate virtual environment
deactivate

pause
