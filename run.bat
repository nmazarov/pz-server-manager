@echo off
REM ============================================
REM PZ Server Manager - Run Script
REM ============================================

cd /d "%~dp0"
echo Starting PZ Server Manager...

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the application
python main.py %*

REM If Python fails, try with py launcher
if errorlevel 1 (
    py -3 main.py %*
)

if errorlevel 1 (
    echo.
    echo Application exited with an error. Check logs\pz_manager.log for details.
    pause
)
