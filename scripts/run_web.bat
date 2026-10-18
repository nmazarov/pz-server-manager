@echo off
chcp 65001 >nul
title PZ Server Manager - Web Dashboard
echo ======================================================
echo   Запуск веб-панели PZ Server Manager...
echo ======================================================

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден в системе! Установите Python 3.
    pause
    exit /b 1
)

cd /d "%~dp0\.."

python -c "import fastapi, uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo Установка необходимых библиотек (FastAPI, Uvicorn, Pydantic)...
    pip install -r requirements-web.txt
)

echo.
echo Открытие веб-панели в браузере...
start http://localhost:8080

echo Запуск веб-сервера на http://0.0.0.0:8080 ...
python web_main.py --host 0.0.0.0 --port 8080 %*
pause
