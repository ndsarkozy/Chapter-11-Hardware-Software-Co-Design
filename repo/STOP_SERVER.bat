@echo off
title Stop Classroom Server
echo Stopping Classroom Server...
taskkill /F /IM python.exe /T >nul 2>&1
net stop mosquitto >nul 2>&1
taskkill /F /IM mosquitto.exe /T >nul 2>&1
echo Done.
timeout /t 2 /nobreak >nul
