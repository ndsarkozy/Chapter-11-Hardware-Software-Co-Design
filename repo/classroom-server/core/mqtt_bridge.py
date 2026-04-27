"""
core/mqtt_bridge.py

Wires MQTT topics to the server-side logic for every class.
Call register_mqtt_handlers(app, class_id, cfg) once per class after
the Flask app and MQTT manager are initialised.

Topic layout (mirrors the working CECS 346 system):

  Device → Server
    <CLASS_ID>/device/announce
        {"mac":"AABBCCDDEEFF","device_id":"esp32_EEFF","firmware":"1.0.0"}

    <CLASS_ID>/device/status/<slot>
        {"slot":3,"ip":"...","rssi":-65,"uptime":120,"temp_c":23.1,
         "humidity_pct":55.2,"fsm_state":"NORMAL","firmware":"1.0.0",
         "free_heap":180000,"student_id":"jsmith"}

    <LESSON_ID>/<slot>/sensor
        {"slot":3,"temp_c":23.1,"humidity_pct":55.2,"fsm_state":"NORMAL","sensor_ok":true}

    <LESSON_ID>/<slot>/answer
        {"slot":3,"token":"abc123","step":2,"answer":"1"}

  Server → Device
    <CLASS_ID>/device/assign/<MAC>
        {"mac":..,"slot":3,"token":"abc123",
         "server_url":"http://192.168.x.x:5000",
         "student_url":"http://.../cecs346/lesson?slot=3&token=abc123"}

    <LESSON_ID>/control/step     {"step":2}
    <LESSON_ID>/control/unlock   {"unlocked_steps":[0,1,2]}
    <LESSON_ID>/control/broadcast {"message":"..."}
"""

import json
import logging
from flask import Flask

log = logging.getLogger("mqtt_bridge")

_registered: set[str] = set()   # guard against double-registration


def register_mqtt_handlers(app: Flask, class_id: str, class_cfg: dict) -> None:
    """
    Register all MQTT handlers for one class.
    Idempotent: calling twice for the same class_id is a no-op.
    """
    if class_id in _registered:
        log.debug(f"[{class_id}] MQTT handlers already registered — skipping")
        return
    _registered.add(class_id)
    from core import sse, session_state, device_state
    from core.device_registry import allocate_slot, verify_token
    from core.scoring_engine import score_submission, append_canvas_row, append_ai_export
    from core.attendance import record_checkin

    mqtt    = app.mqtt
    server_ip   = app.config.get("SERVER_IP", "127.0.0.1")
    server_port = app.config.get("SERVER_PORT", 5000)
    max_slots   = class_cfg.get("slot_count", 50)

    # Use explicit mqtt_prefix if set (must match #define COURSE in firmware)
    # e.g. "C346" for the CECS 346 firmware, "C460" for CECS 460
    LESSON_ID   = class_cfg.get("lesson_id", class_id)
    CLASS_UPPER = class_cfg.get("mqtt_prefix", class_id.upper())

    # ── 1. Device announcement → slot + token assignment ─────────────────────

    @mqtt.on_message(f"{CLASS_UPPER}/device/announce")
    def handle_announce(topic: str, payload: dict):
        if not isinstance(payload, dict):
            return
        mac       = payload.get("mac", "").upper().replace(":", "").replace("-", "")
        device_id = payload.get("device_id", "").strip()
        firmware  = payload.get("firmware", "unknown")

        if not device_id and mac:
            device_id = f"esp32_{mac[-6:]}"

        if not mac and not device_id:
            return

        # Determine the registry key: prefer valid MAC, fall back to device_id
        mac_is_bad = (not mac) or (mac.strip("0") == "") or (len(mac) < 6)
        registry_key = mac if not mac_is_bad else device_id

        if mac_is_bad:
            log.info(
                f"[{class_id}] Device '{device_id}' has bad MAC ({mac or 'empty'}) "
                f"— using device_id as registry key"
            )

        if not registry_key:
            return

        asgn = allocate_slot(class_id, registry_key, device_id, max_slots)
        if not asgn:
            log.warning(f"[{class_id}] No slots available for {registry_key}")
            return

        slot        = asgn["slot"]
        token       = asgn["token"]
        student_url = (
            f"http://{server_ip}:{server_port}"
            f"/{class_id}/lesson/{class_cfg.get('active_lesson','ch01')}"
            f"?slot={slot}&token={token}"
        )
        server_url = f"http://{server_ip}:{server_port}"

        assign_payload = {
            "mac":         mac,
            "slot":        slot,
            "token":       token,
            "server_url":  server_url,
            "student_url": student_url,
        }

        # Publish assignment on the MAC topic (firmware subscribes to this)
        mqtt.publish(
            f"{CLASS_UPPER}/device/assign/{mac}",
            assign_payload
        )
        # Also publish on device_id topic in case MAC was bad but device_id is valid
        if mac_is_bad and device_id:
            mqtt.publish(
                f"{CLASS_UPPER}/device/assign/{device_id}",
                assign_payload
            )

        device_state.update(class_id, slot, {
            "mac":       mac,
            "device_id": device_id,
            "firmware":  firmware,
            "slot":      slot,
        })

        sse.push(class_id, {
            "type":      "device_assigned",
            "slot":      slot,
            "mac":       mac,
            "device_id": device_id,
            "firmware":  firmware,
        })

        log.info(f"[{class_id}] Assigned slot {slot} → {registry_key} ({device_id})")

    # ── 2. Status heartbeat ──────────────────────────────────────────────────

    @mqtt.on_message(f"{CLASS_UPPER}/device/status/+")
    def handle_status(topic: str, payload: dict):
        try:
            slot = int(topic.split("/")[-1])
        except (ValueError, IndexError):
            return

        if not isinstance(payload, dict):
            return

        fields = {k: payload[k] for k in (
            "ip", "rssi", "uptime", "firmware", "free_heap",
            "temp_c", "humidity_pct", "fsm_state", "student_id"
        ) if k in payload}
        fields["slot"] = slot

        device_state.update(class_id, slot, fields)

        sse.push(class_id, {
            "type": "device_status",
            "slot": slot,
            **{k: payload[k] for k in (
                "ip", "rssi", "uptime", "temp_c", "humidity_pct",
                "fsm_state", "student_id"
            ) if k in payload}
        })

    # ── 3. Live sensor telemetry ─────────────────────────────────────────────

    @mqtt.on_message(f"{LESSON_ID}/+/sensor")
    def handle_sensor(topic: str, payload: dict):
        parts = topic.split("/")
        try:
            slot = int(parts[1])
        except (ValueError, IndexError):
            return

        if not isinstance(payload, dict):
            return

        fields = {k: payload[k] for k in (
            "temp_c", "humidity_pct", "temp_filtered", "humidity_filtered",
            "fsm_state", "sensor_ok", "drift_ppm"
        ) if k in payload}

        device_state.update(class_id, slot, fields)

        sse.push(class_id, {
            "type": "sensor",
            "slot": slot,
            **fields,
        })

    # ── 4. Student answers via MQTT ──────────────────────────────────────────

    @mqtt.on_message(f"{LESSON_ID}/+/answer")
    def handle_answer(topic: str, payload: dict):
        parts = topic.split("/")
        try:
            slot = int(parts[1])
        except (ValueError, IndexError):
            return

        if not isinstance(payload, dict):
            return

        token   = payload.get("token", "")
        chapter = payload.get("chapter", class_cfg.get("active_lesson", ""))
        answers = payload.get("answers", {})

        # Support single-answer step-based format from old firmware
        if not answers and "answer" in payload:
            step = payload.get("step", 0)
            try:
                # Numeric step (old firmware): 0-based index → q1, q2, ...
                answers = {f"q{int(step)+1}": str(payload["answer"])}
            except (ValueError, TypeError):
                # String step ID (e.g. q_lab1) — use as-is
                answers = {str(step): str(payload["answer"])}
            chapter = payload.get("chapter", chapter)

        # Token verification
        if not verify_token(class_id, slot, token):
            log.warning(f"[{class_id}] Bad token from slot {slot} – ignored")
            return

        if not chapter:
            log.warning(f"[{class_id}] Answer from slot {slot} missing chapter")
            return

        # Load grading rules
        import os
        grading_path = os.path.join(
            os.path.dirname(__file__), "..", "classes",
            class_id, "lessons", chapter, "grading.json"
        )
        if not os.path.isfile(grading_path):
            log.warning(f"[{class_id}] No grading rules for {chapter}")
            return

        with open(grading_path, encoding="utf-8") as f:
            grading = json.load(f)

        score   = score_submission(answers, grading)
        cfg     = class_cfg
        pct     = score["total"] / score["max"] * 100 if score["max"] else 0
        bonus   = pct >= cfg.get("score_bonus_pct", 90)
        student = f"slot_{slot}"

        import time
        from datetime import datetime

        # Export pipelines
        canvas_path = os.path.join(
            os.path.dirname(__file__), "..", "exports", "canvas_grades.csv"
        )
        ai_path = os.path.join(
            os.path.dirname(__file__), "..", "exports", "ai_grading.json"
        )
        append_canvas_row(canvas_path, student, class_id, chapter, score)
        append_ai_export(ai_path, student, class_id, chapter, answers, score, grading)
        record_checkin(student, class_id, chapter, bonus=bonus)

        # Publish score result back to device
        mqtt.publish(
            f"{LESSON_ID}/{slot}/result",
            {
                "slot":    slot,
                "chapter": chapter,
                "score":   score["total"],
                "max":     score["max"],
                "pct":     round(pct),
                "bonus":   bonus,
            }
        )

        # Record in session state and push to SSE dashboard
        entry = {
            "type":      "submission",
            "slot":      slot,
            "student":   student,
            "chapter":   chapter,
            "score":     score,
            "pct":       round(pct),
            "bonus":     bonus,
            "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
            "source":    "mqtt",
        }
        session_state.record(class_id, entry)
        sse.push(class_id, entry)

        log.info(
            f"[{class_id}] MQTT answer slot={slot} chapter={chapter} "
            f"score={score['total']}/{score['max']} ({round(pct)}%)"
        )
    # ── 5. Live bench telemetry (Ch11 AES timing) ───────────────────────────

    @mqtt.on_message(f"{LESSON_ID}/+/bench")
    def handle_bench(topic: str, payload: dict):
        parts = topic.split("/")
        try:
            slot = int(parts[1])
        except (ValueError, IndexError):
            return

        if not isinstance(payload, dict):
            return

        fields = {k: payload[k] for k in (
            "sw_us", "hw_us", "speedup", "blocks",
            "sw_mb_s", "hw_mb_s"
        ) if k in payload}
        if not fields:
            return

        fields["slot"] = slot
        device_state.update(class_id, slot, fields)

        sse.push(class_id, {
            "type": "bench",
            "slot": slot,
            **fields,
        })

