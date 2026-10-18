@echo off
echo Updating PZ Server Manager...
taskkill /F /IM "PZ Server Manager.exe" >nul 2>&1
timeout /t 1 /nobreak >nul
copy /y "dist\PZ Server Manager.exe" "PZ Server Manager.exe"
echo Done! Launching updated version...
start "" "PZ Server Manager.exe"
