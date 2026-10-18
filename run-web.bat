@echo off
cd /d "%~dp0"
if exist "%~dp0venv\Scripts\activate.bat" (
    call "%~dp0venv\Scripts\activate.bat"
)
python web_main.py --host 0.0.0.0 --port 8080 %*
pause
