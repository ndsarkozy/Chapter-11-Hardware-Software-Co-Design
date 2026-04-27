# CECS Classroom Server — Installation Guide

## No admin rights required. No Mosquitto needed.

The server includes a built-in pure-Python MQTT broker (amqtt) that
starts automatically. No Mosquitto, no DLL errors, no administrator
permissions required for installation.

---

## Installation — Windows

**Prerequisites:**
- Python 3.10+ from https://www.python.org/downloads/
- Tick **"Add Python to PATH"** during the Python installer

**Steps:**
1. Extract this zip anywhere (e.g. `C:\ClassroomServer\`)
2. Double-click **`INSTALL.bat`**
3. Enter your classroom Wi-Fi IP when prompted
4. Press any key to start the server

That's it. No Mosquitto, no admin prompts, no DLL errors.

---

## Installation — Linux / macOS

```bash
chmod +x install.sh && ./install.sh
```

---

## Daily use

**Start:** `Start Classroom Server.bat` (Desktop) or `START_SERVER.bat`
**Stop:**  Close the server window or `Stop Classroom Server.bat`

The MQTT broker starts automatically inside the server process.

---

## URLs

| Page | URL | PIN |
|------|-----|-----|
| CECS 346 Instructor | `http://<your-ip>:5000/cecs346/instructor` | `3460` |
| CECS 346 Projector  | `http://<your-ip>:5000/cecs346/projector`  | — |
| CECS 460 Instructor | `http://<your-ip>:5000/cecs460/instructor` | `4600` |
| CECS 460 Projector  | `http://<your-ip>:5000/cecs460/projector`  | — |

Student URLs are printed to each ESP32's Serial Monitor automatically.

---

## Changing classrooms

Run `CHANGE_IP.bat` and enter the new IP. Restart the server.

---

## Changing instructor PINs

Edit `classroom-server\classes\cecs346\class_config.json` → `"instructor_pin"`
Edit `classroom-server\classes\cecs460\class_config.json` → `"instructor_pin"`

---

## Troubleshooting

**"Port 1883 already in use"** — another MQTT broker is running on this PC.
Either stop it (e.g. `net stop mosquitto`) or let the server use it —
the server will detect the existing broker and skip starting its own.

**ESP32 devices don't connect** — check Windows Firewall allows Python
on private networks. Go to: Windows Defender Firewall → Allow an app →
find Python and tick Private.

**"Module not found" error** — re-run `INSTALL.bat` or run:
`venv\Scripts\pip install -r classroom-server\requirements.txt`
