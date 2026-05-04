"""
core/server.py – Flask application factory.

Creates the app, wires up MQTT, then delegates route registration
to class_loader so each class in classes/ is self-registering.
"""
from flask import Flask
from core import config
from core.mqtt_manager import MQTTManager
from core.class_loader import register_all_classes


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config)
    # Expose network settings to blueprints and MQTT bridge
    app.config.setdefault("SERVER_IP",   config.SERVER_IP)
    app.config.setdefault("SERVER_PORT", config.SERVER_PORT)

    # Boot MQTT
    mqtt = MQTTManager(app)
    app.mqtt = mqtt

    # Auto-register every class found in classes/
    register_all_classes(app)

    @app.route("/")
    def index():
        from flask import jsonify
        classes = [bp.name for bp in app.blueprints.values()]
        return jsonify({"status": "ok", "registered_classes": classes})

    # ── Student tools download ────────────────────────────────────────────────
    import os
    from flask import send_file, abort, jsonify as jfy

    TOOLS_DIR = os.path.join(os.path.dirname(__file__), "..", "tools")
    FIRMWARE_BIN_DIR = os.path.join(os.path.dirname(__file__), "..", "firmware", "bin")
    SKETCHES_DIR = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "hardware", "starter_code"))

    @app.route("/tools/<path:filename>")
    def serve_tool(filename):
        """Serve student-facing tool files (student_client.py, etc.)."""
        safe = os.path.basename(filename)
        path = os.path.join(TOOLS_DIR, safe)
        if not os.path.isfile(path):
            abort(404)
        return send_file(path, as_attachment=True, download_name=safe)

    @app.route("/firmware/bin/<path:filename>")
    def serve_firmware_bin(filename):
        """Serve pre-compiled firmware .bin files for esptool flashing."""
        safe = os.path.basename(filename)
        path = os.path.join(FIRMWARE_BIN_DIR, safe)
        if not os.path.isfile(path):
            abort(404)
        return send_file(path, as_attachment=True, download_name=safe)

    @app.route("/firmware/sketches/")
    def list_firmware_sketches():
        """Manifest of Arduino sketches in hardware/starter_code/."""
        sketches = []
        if os.path.isdir(SKETCHES_DIR):
            for entry in sorted(os.listdir(SKETCHES_DIR)):
                full = os.path.join(SKETCHES_DIR, entry)
                if os.path.isdir(full):
                    files = []
                    for fname in sorted(os.listdir(full)):
                        fpath = os.path.join(full, fname)
                        if os.path.isfile(fpath):
                            files.append({
                                "name": fname,
                                "size": os.path.getsize(fpath),
                                "url": f"/firmware/sketches/{entry}/{fname}",
                            })
                    if files:
                        sketches.append({"sketch": entry, "files": files})
            for fname in sorted(os.listdir(SKETCHES_DIR)):
                fpath = os.path.join(SKETCHES_DIR, fname)
                if os.path.isfile(fpath):
                    sketches.append({
                        "sketch": "",
                        "files": [{
                            "name": fname,
                            "size": os.path.getsize(fpath),
                            "url": f"/firmware/sketches/_root/{fname}",
                        }],
                    })
        return jfy({"sketches": sketches})

    @app.route("/firmware/sketches/<sketch>/<path:filename>")
    def serve_firmware_sketch(sketch, filename):
        """Serve one file from a starter_code sketch folder."""
        safe_file = os.path.basename(filename)
        if sketch == "_root":
            path = os.path.join(SKETCHES_DIR, safe_file)
        else:
            safe_sketch = os.path.basename(sketch)
            path = os.path.join(SKETCHES_DIR, safe_sketch, safe_file)
        if not os.path.isfile(path):
            abort(404)
        return send_file(path, as_attachment=True, download_name=safe_file)

    @app.route("/firmware/bin/")
    def list_firmware_bins():
        """List available firmware binaries (for student client auto-discovery)."""
        if not os.path.isdir(FIRMWARE_BIN_DIR):
            return jfy({"bins": []})
        bins = []
        for f in sorted(os.listdir(FIRMWARE_BIN_DIR)):
            if f.endswith(".bin"):
                full = os.path.join(FIRMWARE_BIN_DIR, f)
                bins.append({
                    "name": f,
                    "size": os.path.getsize(full),
                    "url": f"/firmware/bin/{f}",
                })
        return jfy({"bins": bins})

    return app
