"""
core/device_state.py

In-memory store for live per-device status received via MQTT heartbeats
and sensor telemetry.  Separate from session_state (which tracks lesson
submissions) so the two concerns don't collide.

Devices time out to offline after OFFLINE_TIMEOUT seconds without a
heartbeat.  The sweep is done lazily on read.
"""
import threading
import time

OFFLINE_TIMEOUT = 120   # seconds — generous for browser-only students
                        # (ESP32 heartbeats every 30s; browser polls every 20s as fallback)

_lock    = threading.Lock()
_devices: dict[str, dict] = {}    # class_id -> { slot_str -> {...} }


def _ensure(class_id: str) -> None:
    if class_id not in _devices:
        _devices[class_id] = {}


def update(class_id: str, slot: int | str, fields: dict) -> None:
    """Merge fields into the device record for this slot."""
    ss = str(slot)
    with _lock:
        _ensure(class_id)
        dev = _devices[class_id].setdefault(ss, {"slot": int(slot), "online": False})
        dev.update(fields)
        dev["online"]    = True
        dev["last_seen"] = time.time()


def sweep(class_id: str) -> None:
    """Mark devices offline if they haven't been heard from recently."""
    now = time.time()
    with _lock:
        _ensure(class_id)
        for dev in _devices[class_id].values():
            if now - dev.get("last_seen", 0) > OFFLINE_TIMEOUT:
                dev["online"] = False


def get_all(class_id: str) -> dict:
    """Return a snapshot of all device records (tokens stripped)."""
    sweep(class_id)
    with _lock:
        _ensure(class_id)
        result = {}
        for ss, dev in _devices[class_id].items():
            safe = dict(dev)
            safe.pop("token", None)
            result[ss] = safe
        return result


def get_one(class_id: str, slot: int | str) -> dict | None:
    with _lock:
        _ensure(class_id)
        return dict(_devices[class_id].get(str(slot), {})) or None
