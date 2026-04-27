"""
Classroom Server — entry point.

Starts an MQTT broker (Mosquitto subprocess or embedded amqtt),
then launches the Flask application.

Usage:  python run.py
"""
import asyncio
import logging
import os
import shutil
import subprocess
import sys
import threading
import time

log = logging.getLogger("run")


# ── MQTT broker strategy ─────────────────────────────────────────────────────
# Try in order:
#   1. External Mosquitto already running on 1883 → use it
#   2. Launch Mosquitto as subprocess (if installed)
#   3. Embedded amqtt broker in background thread
# ──────────────────────────────────────────────────────────────────────────────

def _port_in_use(port: int) -> bool:
    """Check if a TCP port is already listening."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _try_external_broker() -> bool:
    """Return True if an MQTT broker is already running on 1883."""
    if _port_in_use(1883):
        log.info("Port 1883 already in use — using existing MQTT broker")
        return True
    return False


_mosquitto_proc = None

def _try_mosquitto_subprocess() -> bool:
    """Try to start Mosquitto as a subprocess. Returns True on success."""
    global _mosquitto_proc
    mosquitto_exe = shutil.which("mosquitto")
    if not mosquitto_exe:
        # Also check common Windows install paths
        for path in [
            r"C:\Program Files\mosquitto\mosquitto.exe",
            r"C:\mosquitto\mosquitto.exe",
        ]:
            if os.path.isfile(path):
                mosquitto_exe = path
                break

    if not mosquitto_exe:
        return False

    # Look for our bundled config
    conf_paths = [
        os.path.join(os.path.dirname(__file__), "..", "mosquitto", "mosquitto.conf"),
        os.path.join(os.path.dirname(__file__), "mosquitto", "mosquitto.conf"),
    ]
    conf = next((p for p in conf_paths if os.path.isfile(p)), None)

    cmd = [mosquitto_exe, "-v"]
    if conf:
        cmd.extend(["-c", os.path.abspath(conf)])
    else:
        # Minimal inline config: listen on all interfaces, allow anonymous
        cmd.extend(["-p", "1883"])

    try:
        _mosquitto_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        time.sleep(1.0)
        if _mosquitto_proc.poll() is not None:
            log.warning("Mosquitto exited immediately")
            return False
        if _port_in_use(1883):
            log.info(f"Mosquitto started (PID {_mosquitto_proc.pid})")
            return True
        log.warning("Mosquitto started but port 1883 not listening")
        return False
    except Exception as e:
        log.warning(f"Could not start Mosquitto: {e}")
        return False


def _try_amqtt_broker() -> bool:
    """Try to start the embedded amqtt broker. Returns True on success."""
    try:
        from amqtt.broker import Broker
    except ImportError:
        log.warning("amqtt not installed — cannot use embedded broker")
        return False

    broker_config = {
        "listeners": {
            "default": {
                "type": "tcp",
                "bind": "0.0.0.0:1883",
                "max_connections": 200,
            }
        },
        "sys_interval": 0,       # disable $SYS topic stats (prevents NoneType error)
        "auth": {
            "allow-anonymous": True,
            "plugins": [],
        },
    }

    started = threading.Event()
    failed  = threading.Event()

    def _broker_thread():
        try:
            # Create a fresh event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def _run():
                broker = Broker(broker_config)
                await broker.start()
                log.info("Embedded MQTT broker running on port 1883")
                started.set()
                # Keep running until the thread is killed
                while True:
                    await asyncio.sleep(3600)

            loop.run_until_complete(_run())
        except OSError as e:
            err = str(e).lower()
            if "address already in use" in err or "10048" in err:
                log.info("Port 1883 already in use — assuming external broker")
                started.set()  # Treat as success
            else:
                log.error(f"MQTT broker failed to start: {e}")
                failed.set()
        except Exception as e:
            log.error(f"MQTT broker error: {e}")
            failed.set()

    t = threading.Thread(target=_broker_thread, name="mqtt-broker", daemon=True)
    t.start()

    # Wait up to 5 seconds for the broker to start
    for _ in range(50):
        if started.is_set():
            return True
        if failed.is_set():
            return False
        time.sleep(0.1)

    # Check if port came up even without the event
    if _port_in_use(1883):
        log.info("Embedded MQTT broker appears to be running")
        return True

    log.error("MQTT broker did not start within 5 seconds")
    return False


def start_broker() -> bool:
    """Start an MQTT broker using the best available method. Returns True on success."""
    # 1. Already running?
    if _try_external_broker():
        return True

    # 2. Try Mosquitto subprocess
    print("  Trying Mosquitto...", end=" ")
    if _try_mosquitto_subprocess():
        print("OK (subprocess)")
        return True
    print("not found")

    # 3. Try embedded amqtt
    print("  Trying embedded amqtt broker...", end=" ")
    if _try_amqtt_broker():
        print("OK")
        return True
    print("FAILED")

    return False


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    print()
    print("  =============================================")
    print("   CECS Classroom Server")
    print("  =============================================")
    print()

    # Start MQTT broker
    print("  Starting MQTT broker on port 1883...")
    broker_ok = start_broker()
    if not broker_ok:
        print()
        print("  !! WARNING: No MQTT broker available !!")
        print("  !! Install Mosquitto: https://mosquitto.org/download/")
        print("  !! Or install amqtt:  pip install amqtt")
        print("  !! Server will start but devices cannot connect.")
        print()

    # Give broker a moment to stabilize
    time.sleep(0.5)

    # Start Flask
    from core.server import create_app
    app = create_app()

    host = "0.0.0.0"
    port = 5000

    # Detect local IP
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "localhost"

    # Also check configured classroom IP
    from core import config
    classroom_ip = config.SERVER_IP

    print()
    print(f"  Server running at:  http://{local_ip}:{port}")
    if local_ip != classroom_ip:
        print(f"  Classroom IP (config): {classroom_ip}")
        print(f"  NOTE: If using classroom Wi-Fi, ensure SERVER_IP in")
        print(f"        core/config.py matches your adapter's IP.")
    print()
    print(f"  ── CECS 346 ─────────────────────────────────────────")
    print(f"  Student Login: http://{local_ip}:{port}/cecs346/login")
    print(f"  Instructor:    http://{local_ip}:{port}/cecs346/instructor  (PIN: 3460)")
    print(f"  Projector:     http://{local_ip}:{port}/cecs346/projector")
    print()
    print(f"  ── CECS 460 ─────────────────────────────────────────")
    print(f"  Student Login: http://{local_ip}:{port}/cecs460/login")
    print(f"  Instructor:    http://{local_ip}:{port}/cecs460/instructor  (PIN: 4600)")
    print(f"  Projector:     http://{local_ip}:{port}/cecs460/projector")
    print()
    print(f"  ── CECS 301 ─────────────────────────────────────────")
    print(f"  Student Login: http://{local_ip}:{port}/cecs301/login")
    print(f"  Instructor:    http://{local_ip}:{port}/cecs301/instructor  (PIN: 3010)")
    print(f"  Projector:     http://{local_ip}:{port}/cecs301/projector")
    print()
    print(f"  Student Device Connector:  student_connect.bat")
    print(f"    (auto-reads seat from ESP32 serial, opens lesson page)")
    print()
    print(f"  MQTT Broker: {'RUNNING' if broker_ok else 'NOT AVAILABLE'}")
    print()
    print("  Press Ctrl+C to stop.")
    print()

    app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
