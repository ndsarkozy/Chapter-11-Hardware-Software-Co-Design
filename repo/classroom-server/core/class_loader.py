"""
core/class_loader.py

Walks the classes/ directory.  For every subfolder that contains a
routes.py and a class_config.json it:

  1. Imports the Blueprint exported as `bp` from routes.py.
  2. Registers it under the URL prefix  /<class_id>/
  3. Attaches the class config to the Blueprint for use in route handlers.
  4. Registers MQTT bridge handlers for device announce/status/sensor/answer.

To add a new class, drop a new folder into classes/ – no edits to
core files are required.
"""
import os
import importlib.util
import json
from flask import Flask, Blueprint


CLASSES_ROOT = os.path.join(os.path.dirname(__file__), "..", "classes")


def _load_class(class_id: str) -> tuple[Blueprint, dict] | None:
    class_dir  = os.path.join(CLASSES_ROOT, class_id)
    routes_py  = os.path.join(class_dir, "routes.py")
    config_fp  = os.path.join(class_dir, "class_config.json")

    if not os.path.isfile(routes_py) or not os.path.isfile(config_fp):
        return None

    with open(config_fp) as f:
        class_cfg = json.load(f)

    spec   = importlib.util.spec_from_file_location(f"classes.{class_id}.routes", routes_py)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    bp: Blueprint = getattr(module, "bp", None)
    if bp is None:
        raise ImportError(f"classes/{class_id}/routes.py must export a Blueprint named 'bp'")

    bp.class_config = class_cfg
    return bp, class_cfg


def register_all_classes(app: Flask) -> None:
    if not os.path.isdir(CLASSES_ROOT):
        app.logger.warning("classes/ directory not found – no classes loaded")
        return

    from core.mqtt_bridge import register_mqtt_handlers

    for entry in sorted(os.scandir(CLASSES_ROOT), key=lambda e: e.name):
        if not entry.is_dir():
            continue
        result = _load_class(entry.name)
        if result is None:
            continue
        bp, cfg = result
        prefix = f"/{entry.name}"
        app.register_blueprint(bp, url_prefix=prefix)
        app.logger.info(f"Registered class '{cfg.get('name', entry.name)}' at {prefix}/")

        # Wire MQTT bridge for this class
        try:
            register_mqtt_handlers(app, entry.name, cfg)
            app.logger.info(f"MQTT bridge registered for '{entry.name}'")
        except Exception as e:
            app.logger.warning(f"MQTT bridge failed for '{entry.name}': {e}")
