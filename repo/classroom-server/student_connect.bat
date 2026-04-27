@echo off
REM ============================================================
REM  CECS Classroom — Student Device Connector
REM  Connects to your ESP32 serial port and opens the lesson page.
REM ============================================================
title CECS Student Connector
cd /d "%~dp0tools"

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Check for pyserial
python -c "import serial" >nul 2>&1
if errorlevel 1 (
    echo Installing pyserial...
    python -m pip install pyserial --quiet
)

python student_client.py
