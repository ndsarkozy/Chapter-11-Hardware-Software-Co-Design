#!/bin/bash
# Classroom Server Installer — Linux / macOS
# No admin required. MQTT broker is included (pure Python).

set -e
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$INSTALL_DIR/classroom-server"
VENV_DIR="$INSTALL_DIR/venv"

GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

echo ""
echo "============================================================"
echo "  CECS Classroom Server Installer (Linux / macOS)"
echo "  No Mosquitto needed — MQTT broker included."
echo "============================================================"
echo ""

# Python check
echo "[1/3] Checking Python..."
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}python3 not found. Install Python 3.11+${NC}"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-venv"
    echo "  macOS:         brew install python3"
    exit 1
fi
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "  ${GREEN}Python $PY_VER OK${NC}"

# Virtual environment
echo ""
echo "[2/3] Setting up virtual environment..."
if [ -f "$VENV_DIR/bin/python" ]; then
    echo "  Already exists."
else
    python3 -m venv "$VENV_DIR"
    echo -e "  ${GREEN}Created.${NC}"
fi

echo "  Installing packages (Flask, paho-mqtt, amqtt)..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet --disable-pip-version-check
"$VENV_DIR/bin/pip" install -r "$SERVER_DIR/requirements.txt" --disable-pip-version-check
echo -e "  ${GREEN}Packages installed.${NC}"

# Configure IP
echo ""
echo "[3/3] Network configuration..."
echo ""
echo "  Current IP addresses:"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    hostname -I 2>/dev/null | tr ' ' '\n' | grep -v '^$' | sed 's/^/    /'
else
    ifconfig 2>/dev/null | grep 'inet ' | awk '{print "    "$2}'
fi
echo ""
read -p "  Enter classroom Wi-Fi IP (e.g. 192.168.8.10): " SERVER_IP
[ -z "$SERVER_IP" ] && SERVER_IP="192.168.8.10"

python3 -c "
import re
p = '$SERVER_DIR/core/config.py'
c = open(p).read()
c = re.sub(r'SERVER_IP\s*=\s*[\"\'].*?[\"\']', 'SERVER_IP   = \"$SERVER_IP\"', c)
open(p,'w').write(c)
print('  SERVER_IP set to: $SERVER_IP')
"

# Write start/stop scripts
cat > "$INSTALL_DIR/start.sh" << STARTEOF
#!/bin/bash
cd "\$(dirname "\$0")/classroom-server"
"\$(dirname "\$0")/venv/bin/python" run.py
STARTEOF
chmod +x "$INSTALL_DIR/start.sh"

cat > "$INSTALL_DIR/stop.sh" << STOPEOF
#!/bin/bash
pkill -f "run.py" 2>/dev/null && echo "Stopped." || echo "Not running."
STOPEOF
chmod +x "$INSTALL_DIR/stop.sh"

echo ""
echo "============================================================"
echo -e "  ${GREEN}Installation complete!${NC}"
echo "============================================================"
echo ""
echo "  Start: ./start.sh"
echo "  Stop:  ./stop.sh  (or Ctrl+C)"
echo ""
echo "  CECS 346: http://$SERVER_IP:5000/cecs346/instructor  (PIN: 3460)"
echo "  CECS 460: http://$SERVER_IP:5000/cecs460/instructor  (PIN: 4600)"
echo ""
read -p "  Start now? [Y/n] " ans
[[ "$ans" =~ ^[Nn] ]] || bash "$INSTALL_DIR/start.sh"
