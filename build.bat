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

echo [1/5] Checking Python version...
python --version

REM Create virtual environment if not exists
if not exist "venv" (
    echo [2/5] Creating virtual environment...
    python -m venv venv
) else (
    echo [2/5] Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo [3/5] Installing dependencies...
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

REM Build executable with PyInstaller
echo [4/5] Building executable folder with PyInstaller...
echo.

pyinstaller --clean --noconfirm pz_server_manager.spec

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed!
    pause
    exit /b 1
)

REM Optional: Compile Inno Setup installer if ISCC is installed
echo [5/5] Checking for Inno Setup compiler (ISCC.exe)...
set ISCC_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if exist %ISCC_PATH% (
    echo Compiling Windows installer with Inno Setup...
    %ISCC_PATH% installer.iss
    if errorlevel 0 (
        echo Installer created: installer_output\PZ_Server_Manager_Setup.exe
    )
) else (
    echo [INFO] Inno Setup compiler not found. Skipping .exe setup installer creation.
    echo (You can download Inno Setup 6 to compile installer.iss into PZ_Server_Manager_Setup.exe)
)

echo.
echo ========================================
echo   Build Complete!
echo ========================================
echo.
echo Standalone Executable Folder:
echo   dist\PZ Server Manager\PZ Server Manager.exe
echo.

REM Deactivate virtual environment
deactivate

pause
