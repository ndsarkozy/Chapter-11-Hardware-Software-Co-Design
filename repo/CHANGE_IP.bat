@echo off
setlocal
echo.
echo Current addresses:
ipconfig | findstr /i "IPv4"
echo.
set /p NEW_IP="Enter new IP address: "
if "%NEW_IP%"=="" goto :eof
"C:\complete-build\venv\Scripts\python.exe" -c "import re; p=r'C:\complete-build\classroom-server\core\config.py'; c=open(p).read(); c=re.sub(r'SERVER_IP\s*=\s*[\"\'].*?[\"\']','SERVER_IP   = \"%NEW_IP%\"',c); open(p,'w').write(c)"
echo Done. Restart the server.
pause
