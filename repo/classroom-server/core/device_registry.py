"""
core/device_registry.py

Manages the MAC → {slot, token} mapping for all classes.
Each class gets its own mappings file so rosters are independent.

Features:
- Persistent JSON storage (survives server restart)
- Thread-safe allocation
- Token verification for student page access and answer submission
- Slot re-use: if a device reconnects with the same MAC it gets the same slot
"""
import hashlib
import json
import os
import threading
import time

_lock     = threading.Lock()
_mappings: dict[str, dict] = {}          # class_id -> {MAC -> {slot, token, ...}}
_dir      = os.path.join(os.path.dirname(__file__), "..", "exports")


def _path(class_id: str) -> str:
    os.makedirs(_dir, exist_ok=True)
    return os.path.join(_dir, f"mappings_{class_id}.json")


def _load(class_id: str) -> dict:
    p = _path(class_id)
    if os.path.isfile(p):
        try:
            with open(p) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save(class_id: str) -> None:
    with open(_path(class_id), "w") as f:
        json.dump(_mappings[class_id], f, indent=2)


def _ensure(class_id: str) -> None:
    if class_id not in _mappings:
        _mappings[class_id] = _load(class_id)


# ── Public API ────────────────────────────────────────────────────────────────

def allocate_slot(class_id: str, mac: str, device_id: str,
                  max_slots: int = 50) -> dict | None:
    """
    Allocate (or retrieve existing) slot for a MAC address.
    Returns the full mapping dict {slot, token, device_id, mac} or None if full.
    Rejects empty or all-zero MACs to prevent multiple devices sharing slot 1.
    """
    mac = mac.upper().replace(":", "").replace("-", "")
    # Reject invalid MACs: empty, all zeros, or too short
    if not mac or mac.strip("0") == "" or len(mac) < 4:
        return None
    with _lock:
        _ensure(class_id)
        mapping = _mappings[class_id]

        # Auto-clean any existing all-zero entries from old data
        bad_keys = [k for k in mapping if k.strip("0") == ""]
        if bad_keys:
            for k in bad_keys:
                del mapping[k]
            _save(class_id)

        if mac in mapping:
            # Update device_id in case it changed
            mapping[mac]["device_id"] = device_id
            _save(class_id)
            return mapping[mac]

        used = {v["slot"] for v in mapping.values()}
        for slot in range(1, max_slots + 1):
            if slot not in used:
                token = hashlib.sha256(
                    f"{mac}{slot}{time.time()}".encode()
                ).hexdigest()[:16]
                mapping[mac] = {
                    "slot":      slot,
                    "token":     token,
                    "device_id": device_id,
                    "mac":       mac,
                }
                _save(class_id)
                return mapping[mac]
    return None


def verify_token(class_id: str, slot: int | str, token: str) -> bool:
    """Return True if (slot, token) is a valid pair for this class."""
    with _lock:
        _ensure(class_id)
        for asgn in _mappings[class_id].values():
            if str(asgn["slot"]) == str(slot) and asgn["token"] == token:
                return True
    return False


def get_all(class_id: str) -> list[dict]:
    """Return all mappings for a class (tokens included – server-side only)."""
    with _lock:
        _ensure(class_id)
        return list(_mappings[class_id].values())


def reset(class_id: str) -> None:
    """Wipe all slot assignments for a class (instructor reset)."""
    with _lock:
        _mappings[class_id] = {}
        _save(class_id)


def lookup_by_slot(class_id: str, slot: int | str) -> dict | None:
    """Find the mapping entry for a given slot number. Returns dict or None."""
    with _lock:
        _ensure(class_id)
        for asgn in _mappings[class_id].values():
            if str(asgn["slot"]) == str(slot):
                return dict(asgn)
    return None


def delete_by_mac(class_id: str, mac: str) -> bool:
    """Remove a specific MAC entry from the mappings. Returns True if found."""
    mac = mac.upper().replace(":", "").replace("-", "")
    with _lock:
        _ensure(class_id)
        if mac in _mappings[class_id]:
            del _mappings[class_id][mac]
            _save(class_id)
            return True
    return False
