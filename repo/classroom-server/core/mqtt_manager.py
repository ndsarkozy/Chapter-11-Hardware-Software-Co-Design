"""
core/mqtt_manager.py

Thin wrapper around paho-mqtt.  Subscribes to classroom/# and
dispatches incoming messages to registered handlers.

Compatible with paho-mqtt 1.x and 2.x.

Usage inside a route handler or background thread:
    from flask import current_app
    current_app.mqtt.publish("classroom/slot/3/response", payload)
"""
import json
import threading
from typing import Callable

try:
    import paho.mqtt.client as mqtt_client
    PAHO_AVAILABLE = True
    # Detect paho-mqtt version (v2 requires CallbackAPIVersion)
    PAHO_V2 = hasattr(mqtt_client, "CallbackAPIVersion")
except ImportError:
    PAHO_AVAILABLE = False
    PAHO_V2 = False


class MQTTManager:
    def __init__(self, app=None):
        self._handlers: dict[str, list[Callable]] = {}
        self._client = None
        self._connected = False
        self._app = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        self._app = app
        broker = app.config.get("MQTT_BROKER", "localhost")
        port   = app.config.get("MQTT_PORT", 1883)
        topic  = app.config.get("MQTT_TOPIC", "classroom/#")

        if not PAHO_AVAILABLE:
            app.logger.warning("paho-mqtt not installed – MQTT disabled (pip install paho-mqtt)")
            return

        # Create client – paho-mqtt v2 requires CallbackAPIVersion
        if PAHO_V2:
            self._client = mqtt_client.Client(
                callback_api_version=mqtt_client.CallbackAPIVersion.VERSION1
            )
        else:
            self._client = mqtt_client.Client()

        self._client.on_connect    = self._on_connect
        self._client.on_message    = self._on_message
        self._client.on_disconnect = self._on_disconnect

        self._broker = broker
        self._port   = port
        self._topic  = topic

        self._connect_with_retry(app)

    def _connect_with_retry(self, app):
        """Connect to broker with retry logic (broker may still be starting)."""
        import time

        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            try:
                self._client.connect(self._broker, self._port, keepalive=60)
                # Do NOT subscribe here — _on_connect handles all subscriptions
                # so that reconnects are also covered without duplicates.
                t = threading.Thread(target=self._client.loop_forever, daemon=True)
                t.start()
                app.logger.info(f"MQTT connected to {self._broker}:{self._port}, topic={self._topic}")
                return
            except Exception as e:
                if attempt < max_attempts:
                    app.logger.info(f"MQTT connect attempt {attempt}/{max_attempts} failed, retrying in 1s...")
                    time.sleep(1)
                else:
                    app.logger.warning(f"MQTT connection failed after {max_attempts} attempts: {e}")

    # ── public API ──────────────────────────────────────────────────────────

    def publish(self, topic: str, payload: dict | str) -> None:
        if not self._client or not self._connected:
            return
        data = json.dumps(payload) if isinstance(payload, dict) else payload
        self._client.publish(topic, data)

    def on_message(self, topic_pattern: str):
        """Decorator: @mqtt.on_message('classroom/+/answer')

        Registers a Python-level dispatch handler.  The broker subscription is
        the single broad wildcard set in _on_connect; no per-pattern MQTT
        subscribe is needed here (and adding one would create overlapping
        subscriptions that cause duplicate message delivery).
        """
        def decorator(fn: Callable):
            self._handlers.setdefault(topic_pattern, []).append(fn)
            return fn
        return decorator

    # ── private callbacks ────────────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, rc):
        self._connected = (rc == 0)
        if self._connected:
            # Subscribe only to the broad wildcard.  This single subscription
            # covers every topic the handlers care about, so there is no overlap
            # between the wildcard and the individual handler patterns.
            # Subscribing to BOTH caused Mosquitto to deliver each matching
            # message twice (once per overlapping subscription), producing
            # duplicate handler calls on every incoming message.
            if hasattr(self, '_topic'):
                client.subscribe(self._topic)

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False

    def _on_message(self, client, userdata, msg):
        topic   = msg.topic
        try:
            payload = json.loads(msg.payload.decode())
        except Exception:
            payload = msg.payload.decode()

        for pattern, handlers in self._handlers.items():
            if mqtt_client.topic_matches_sub(pattern, topic):
                for h in handlers:
                    try:
                        h(topic, payload)
                    except Exception as e:
                        if self._app:
                            self._app.logger.error(f"MQTT handler error on {topic}: {e}")
