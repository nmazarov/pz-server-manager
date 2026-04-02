@echo off
REM ============================================
REM PZ Server Manager - Run Script
REM ============================================

echo Starting PZ Server Manager...

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the application
python main.py

REM If Python fails, try with py launcher
if errorlevel 1 (
    py -3 main.py
)

pause
