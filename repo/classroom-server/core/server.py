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
