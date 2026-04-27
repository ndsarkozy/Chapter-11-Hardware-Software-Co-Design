@echo off
setlocal enabledelayedexpansion
title Classroom Server Installer
color 0A

echo.
echo ============================================================
echo   CECS Classroom Server -- Installer
echo   Embedded Systems I (CECS 346) and SoC Design (CECS 460)
echo ============================================================
echo.
echo   No admin rights required. No Mosquitto needed.
echo   An MQTT broker is included and starts with the server.
echo.

set "INSTALL_DIR=%~dp0"
set "SERVER_DIR=%INSTALL_DIR%classroom-server"
set "VENV_DIR=%INSTALL_DIR%venv"

:: ============================================================
:: Step 1: Check Python
:: ============================================================
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 goto :no_python

for /f "tokens=2 delims= " %%v in ('python --version') do set PY_VER=%%v
echo   Found Python %PY_VER%
goto :python_ok

:no_python
echo.
echo   ERROR: Python not found.
echo.
echo   Install Python 3.11+ from https://www.python.org/downloads/
echo   IMPORTANT: tick "Add Python to PATH" during install.
echo.
pause
exit /b 1

:python_ok

:: ============================================================
:: Step 2: Create virtual environment
:: ============================================================
echo.
echo [2/4] Setting up Python virtual environment...
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo   Already exists -- skipping.
    goto :venv_ok
)
python -m venv "%VENV_DIR%"
if errorlevel 1 goto :venv_fail
echo   Created.
goto :venv_ok

:venv_fail
echo   ERROR: Could not create virtual environment.
pause
exit /b 1

:venv_ok

:: ============================================================
:: Step 3: Install packages
:: ============================================================
echo.
echo [3/4] Installing packages (Flask, paho-mqtt, amqtt broker)...
echo   Requires internet. Please wait...
echo.

:: Upgrade pip silently, suppress the "new version available" notice
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip --quiet --disable-pip-version-check 2>nul

:: Install all requirements, suppress version check notice
"%VENV_DIR%\Scripts\pip" install -r "%SERVER_DIR%\requirements.txt" --disable-pip-version-check

if errorlevel 1 goto :pip_fail
echo.
echo   Packages installed OK.
goto :pip_ok

:pip_fail
echo.
echo   ERROR: Installation failed. Check internet connection.
pause
exit /b 1

:pip_ok

:: ============================================================
:: Step 4: Configure IP and create shortcuts
:: ============================================================
echo.
echo [4/4] Configuring server IP address...
echo.
echo   Your current network addresses:
ipconfig | findstr /i "IPv4"
echo.
set /p SERVER_IP="  Enter your classroom Wi-Fi IP (e.g. 192.168.8.10): "
if "%SERVER_IP%"=="" set SERVER_IP=192.168.8.10

:: Update config.py
"%VENV_DIR%\Scripts\python.exe" -c "import re; p=r'%SERVER_DIR%\core\config.py'; c=open(p).read(); c=re.sub(r'SERVER_IP\s*=\s*[\"\'].*?[\"\']','SERVER_IP   = \"%SERVER_IP%\"',c); open(p,'w').write(c); print('  SERVER_IP set to: %SERVER_IP%')"

:: Write START_SERVER.bat
call :write_start "%INSTALL_DIR%START_SERVER.bat"

:: Desktop shortcuts
set "DESKTOP=%USERPROFILE%\Desktop"
call :write_start "%DESKTOP%\Start Classroom Server.bat"

(echo @echo off
echo taskkill /F /IM python.exe /T ^>nul 2^>^&1
echo echo Stopped.
echo timeout /t 2 /nobreak ^>nul) > "%DESKTOP%\Stop Classroom Server.bat"

(echo @echo off & echo start http://%SERVER_IP%:5000/cecs346/instructor) > "%DESKTOP%\Open CECS346 Instructor.bat"
(echo @echo off & echo start http://%SERVER_IP%:5000/cecs346/projector)  > "%DESKTOP%\Open CECS346 Projector.bat"
(echo @echo off & echo start http://%SERVER_IP%:5000/cecs460/instructor) > "%DESKTOP%\Open CECS460 Instructor.bat"
(echo @echo off & echo start http://%SERVER_IP%:5000/cecs460/projector)  > "%DESKTOP%\Open CECS460 Projector.bat"

:: Write CHANGE_IP helper
(echo @echo off
echo setlocal
echo echo.
echo echo Current addresses:
echo ipconfig ^| findstr /i "IPv4"
echo echo.
echo set /p NEW_IP="Enter new IP address: "
echo if "%%NEW_IP%%"=="" goto :eof
echo "%VENV_DIR%\Scripts\python.exe" -c "import re; p=r'%SERVER_DIR%\core\config.py'; c=open(p).read(); c=re.sub(r'SERVER_IP\s*=\s*[\"\'].*?[\"\']','SERVER_IP   = \"%%NEW_IP%%\"',c); open(p,'w').write(c)"
echo echo Done. Restart the server.
echo pause) > "%INSTALL_DIR%CHANGE_IP.bat"

:: ============================================================
:: Done
:: ============================================================
echo.
echo ============================================================
echo   Installation complete!
echo ============================================================
echo.
echo   Server IP  : %SERVER_IP%:5000
echo   CECS 346   : http://%SERVER_IP%:5000/cecs346/instructor  (PIN: 3460)
echo   CECS 460   : http://%SERVER_IP%:5000/cecs460/instructor  (PIN: 4600)
echo.
echo   Desktop shortcuts created.
echo   To start: double-click "Start Classroom Server" on Desktop.
echo.
echo   The MQTT broker starts automatically with the server --
echo   no Mosquitto installation needed.
echo.
echo   Press any key to start the server now...
pause
call "%INSTALL_DIR%START_SERVER.bat"
goto :eof

:: ── Subroutine: write the start script ──────────────────────────────────────
:write_start
(echo @echo off
echo title Classroom Server
echo color 0A
echo echo.
echo echo   =============================================
echo echo    CECS Classroom Server
echo echo    http://%SERVER_IP%:5000
echo echo   =============================================
echo echo.
echo echo   CECS 346: http://%SERVER_IP%:5000/cecs346/instructor  ^(PIN: 3460^)
echo echo   CECS 460: http://%SERVER_IP%:5000/cecs460/instructor  ^(PIN: 4600^)
echo echo.
echo echo   Press Ctrl+C to stop.
echo echo.
echo cd /d "%SERVER_DIR%"
echo "%VENV_DIR%\Scripts\python.exe" run.py
echo pause) > %1
goto :eof
