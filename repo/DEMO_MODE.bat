@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title CECS 460 Ch.11 - Demo Mode

echo.
echo ================================================================
echo   CECS 460 Chapter 11 - Hardware/Software Co-Design
echo   Final Expo Demo Launcher
echo   Nathan Sarkozy and Christian Vanegas
echo ================================================================
echo.

:: ── Detect the LAN IP via PowerShell ─────────────────────────────────────
:: Prefers DHCP/manual IPv4 addresses on physical adapters; ignores APIPA,
:: virtual switches, and loopback. Falls back to localhost if nothing found.
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "$ip = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue ^| Where-Object { $_.PrefixOrigin -in 'Dhcp','Manual' -and $_.IPAddress -notlike '169.*' -and $_.IPAddress -ne '127.0.0.1' } ^| Sort-Object -Property InterfaceMetric ^| Select-Object -First 1).IPAddress; if (-not $ip) { 'localhost' } else { $ip }"`) do set "DETECTED_IP=%%i"

if "%DETECTED_IP%"=="" set "DETECTED_IP=localhost"

echo Detected server IP: %DETECTED_IP%
echo (set in firmware MQTT_HOST: this should match)
echo.
choice /c YN /n /m "Use this IP? [Y/N] (N to enter another): "
if errorlevel 2 (
  set /p DETECTED_IP="Enter the IP to use: "
  if "!DETECTED_IP!"=="" set "DETECTED_IP=localhost"
)

set "BASE_URL=http://%DETECTED_IP%:5000/cecs460"
echo.
echo Demo URLs:
echo   Dashboard:  %BASE_URL%/instructor   (PIN: 4600)
echo   Projector:  %BASE_URL%/projector
echo   Student:    %BASE_URL%/login
echo.

:: ── Step 1: Stop any old server processes ────────────────────────────────
echo [1/5] Stopping any previous classroom server...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 1 /nobreak >nul

:: ── Step 2: Start server in its own window (so closing this one won't kill it) -
echo [2/5] Starting classroom server in a new window...
start "Classroom Server (Demo)" cmd /k "cd /d "%~dp0classroom-server" && set PYTHONIOENCODING=utf-8 && set PYTHONUTF8=1 && python run.py"

:: ── Step 3: Wait for the server to respond on :5000 ──────────────────────
echo [3/5] Waiting for the server to come online...
set /a TRIES=0
:wait_loop
timeout /t 1 /nobreak >nul
set /a TRIES+=1
if %TRIES% gtr 25 goto :timeout
powershell -NoProfile -Command "try { (Invoke-WebRequest 'http://localhost:5000/' -UseBasicParsing -TimeoutSec 1) ^| Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 goto :wait_loop

echo       Server is up.

:: ── Step 4: Reset session state for a clean demo ─────────────────────────
echo [4/5] Resetting session state for a clean demo...
powershell -NoProfile -Command "try { Invoke-RestMethod -Method Post -Uri 'http://localhost:5000/cecs460/session/clear' -ContentType 'application/json' -Body '{\"pin\":\"4600\"}' ^| Out-Null } catch { Write-Host '  (skipped - server may still be initializing)' }" 2>nul

:: ── Step 5: Open the demo windows ────────────────────────────────────────
echo [5/5] Opening demo windows...
start "" "%~dp0presentation.html"
timeout /t 1 /nobreak >nul
start "" "%BASE_URL%/instructor"
timeout /t 1 /nobreak >nul
start "" "%BASE_URL%/projector"

echo.
echo ================================================================
echo   DEMO READY
echo ================================================================
echo.
echo   Presentation:   arrow keys navigate
echo                   S = presenter notes
echo                   D = demo links
echo                   F = fullscreen
echo                   Esc = close overlays
echo.
echo   Dashboard PIN:  4600
echo   Active lesson:  ch11Final
echo.
echo   Bench setup checklist:
echo     [ ] Step 4 firmware loaded with USE_DMA = 0
echo     [ ] Pot wired GPIO 34, LCD on GPIO 21/22
echo     [ ] Arduino IDE open with Serial Monitor at 115200
echo     [ ] ESP32 connected to DEEZ WiFi (or your demo SSID)
echo     [ ] MQTT_HOST in step4_accelerator.ino = %DETECTED_IP%
echo.
echo   To stop the server:    STOP_SERVER.bat
echo   To restart cleanly:    re-run DEMO_MODE.bat
echo.
echo ================================================================
echo.
pause
goto :eof

:timeout
echo.
echo ERROR: Server did not start within 25 seconds.
echo Check the "Classroom Server (Demo)" window for Python errors.
echo Common causes:
echo   - Port 5000 already in use (something else binding it)
echo   - Missing Python deps - run install.sh / INSTALL.bat first
echo   - Mosquitto not installed (server will still start, but no MQTT)
echo.
pause
