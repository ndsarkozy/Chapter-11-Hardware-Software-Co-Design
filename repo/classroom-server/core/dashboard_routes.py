"""
core/dashboard_routes.py

Call register_dashboard_routes(bp, class_id, lessons_dir) from any class
routes.py to get all dashboard endpoints for free.

Registered routes (all prefixed by the Blueprint's url_prefix):
    GET  /instructor          – instructor dashboard
    GET  /projector           – projector display
    GET  /stream              – SSE event stream
    GET  /api/state           – public device + lesson state (JSON)
    GET  /api/state/instructor – full state incl. scores (PIN required)
    GET  /api/verify          – verify slot+token
    POST /set-lesson          – change active lesson  { "chapter": "ch11" }
    POST /lesson/unlock-step  – unlock a step  { "pin":..., "step": 2 }
    POST /lesson/step         – jump to unlocked step  { "pin":..., "step": 2 }
    POST /lesson/broadcast    – broadcast message  { "pin":..., "message": "..." }
    POST /session/clear       – wipe in-memory session state (PIN required)
    POST /devices/reset       – wipe all slot assignments (PIN required)
    GET  /export/canvas       – download canvas_grades.csv
    GET  /export/ai           – download ai_grading.json
    GET  /lesson/<ch>/reference/<filename> – serve reference code files
"""
import json
import os
import queue

from flask import (
    Blueprint, Response, current_app, jsonify,
    render_template, request, send_file, stream_with_context,
)

from core import sse, session_state, device_state
from core.device_registry import get_all as registry_get_all, verify_token, reset as registry_reset, delete_by_mac


def _verify_pin(class_cfg: dict) -> bool:
    d   = request.get_json(force=True, silent=True) or {}
    pin = d.get("pin") or request.args.get("pin", "")
    return pin == class_cfg.get("instructor_pin", "")


def register_dashboard_routes(bp: Blueprint, class_id: str, lessons_dir: str) -> None:

    # ── SSE stream ────────────────────────────────────────────────────────────

    @bp.route("/stream")
    def _stream():
        snapshot     = session_state.get_all(class_id)
        devices_snap = device_state.get_all(class_id)
        q = sse.subscribe(class_id)

        def generate():
            yield f"data: {json.dumps({'type':'snapshot','submissions':snapshot,'devices':devices_snap})}\n\n"
            try:
                while True:
                    try:
                        msg = q.get(timeout=20)
                        yield msg
                    except queue.Empty:
                        yield ": heartbeat\n\n"
            except GeneratorExit:
                sse.unsubscribe(class_id, q)

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # ── Public state API (used by student pages too) ──────────────────────────

    @bp.route("/api/state")
    def _api_state():
        # Browser heartbeat: if a student page passes its slot, refresh
        # that device's last_seen so browser-only students stay "online".
        # Harmless for ESP32 classes (they heartbeat via MQTT anyway).
        slot = request.args.get("slot")
        if slot is not None:
            # Enrich with student name from the persistent registry so that
            # browser-only students re-appear correctly after a server restart
            # (device_state is in-memory; device_registry survives restarts).
            from core.device_registry import lookup_by_slot as _reg_lookup
            reg = _reg_lookup(class_id, slot)
            fields: dict = {}
            if reg and reg.get("device_id"):
                fields["student_id"] = reg["device_id"]
            device_state.update(class_id, slot, fields)

        device_state.sweep(class_id)
        devs    = device_state.get_all(class_id)
        # Load active lesson step state from session
        ss      = session_state.get_lesson_state(class_id)
        return jsonify({"devices": devs, "lesson": ss})

    # ── Instructor state API (PIN required) ───────────────────────────────────

    @bp.route("/api/state/instructor")
    def _api_state_instructor():
        if not _verify_pin(bp.class_config):
            return jsonify({"error": "Unauthorized"}), 403
        device_state.sweep(class_id)
        devs    = device_state.get_all(class_id)
        ss      = session_state.get_lesson_state(class_id)
        scores  = session_state.get_scores(class_id)
        resp_counts = session_state.get_response_counts(class_id)
        return jsonify({
            "devices":         devs,
            "lesson":          ss,
            "scores":          scores,
            "response_counts": resp_counts,
        })

    # ── Token verification ────────────────────────────────────────────────────

    @bp.route("/api/verify")
    def _api_verify():
        slot  = request.args.get("slot", "")
        token = request.args.get("token", "")
        if verify_token(class_id, slot, token):
            return jsonify({"ok": True, "slot": slot})
        return jsonify({"ok": False}), 403

    @bp.route("/api/verify_pin")
    def _api_verify_pin():
        pin = request.args.get("pin", "")
        return jsonify({"ok": pin == bp.class_config.get("instructor_pin", "")})

    # ── Instructor page ───────────────────────────────────────────────────────

    @bp.route("/instructor")
    def _instructor():
        cfg = bp.class_config
        chapters = sorted(
            e.name for e in os.scandir(lessons_dir)
            if e.is_dir() and os.path.isfile(os.path.join(e.path, "lesson.json"))
        )
        # Load step data for active lesson
        active_ch = cfg.get("active_lesson", "")
        steps = _load_steps(lessons_dir, active_ch)
        questions = _load_questions(lessons_dir, active_ch)
        return render_template(
            "instructor.html",
            class_id=class_id,
            class_name=cfg.get("name", class_id),
            slot_count=cfg.get("slot_count", 30),
            active_lesson=active_ch,
            chapters=chapters,
            steps=steps,
            questions=questions,
            has_pin=bool(cfg.get("instructor_pin")),
        )

    # ── Projector page ────────────────────────────────────────────────────────

    @bp.route("/projector")
    def _projector():
        cfg = bp.class_config
        active_ch = cfg.get("active_lesson", "")
        steps = _load_steps(lessons_dir, active_ch)
        questions = _load_questions(lessons_dir, active_ch)
        return render_template(
            "projector.html",
            class_id=class_id,
            class_name=cfg.get("name", class_id),
            slot_count=cfg.get("slot_count", 30),
            active_lesson=active_ch,
            steps=steps,
            questions=questions,
            browser_only=cfg.get("browser_only", False),
        )

    # ── Lesson step control ───────────────────────────────────────────────────

    @bp.route("/lesson/unlock-step", methods=["POST"])
    def _unlock_step():
        if not _verify_pin(bp.class_config):
            return jsonify({"error": "Unauthorized"}), 403
        d    = request.get_json(force=True, silent=True) or {}
        step = int(d.get("step", 0))
        cfg  = bp.class_config
        total = len(_load_steps(lessons_dir, cfg.get("active_lesson", "")))
        if step < 0 or (total and step >= total):
            return jsonify({"error": "Invalid step"}), 400

        unlocked = session_state.unlock_step(class_id, step)

        lesson_id = cfg.get("lesson_id", class_id)
        current_app.mqtt.publish(
            f"{lesson_id}/control/step",
            {"step": step}
        )
        current_app.mqtt.publish(
            f"{lesson_id}/control/unlock",
            {"unlocked_steps": unlocked}
        )
        sse.push(class_id, {"type": "step_unlocked", "step": step, "unlocked_steps": unlocked})
        return jsonify({"ok": True, "step": step, "unlocked_steps": unlocked})

    @bp.route("/lesson/step", methods=["POST"])
    def _set_step():
        if not _verify_pin(bp.class_config):
            return jsonify({"error": "Unauthorized"}), 403
        d    = request.get_json(force=True, silent=True) or {}
        step = int(d.get("step", 0))
        unlocked = session_state.get_lesson_state(class_id).get("unlocked_steps", [0])
        if step not in unlocked:
            return jsonify({"error": "Step not unlocked"}), 400
        session_state.set_active_step(class_id, step)
        lesson_id = bp.class_config.get("lesson_id", class_id)
        current_app.mqtt.publish(f"{lesson_id}/control/step", {"step": step})
        sse.push(class_id, {"type": "step_changed", "step": step})
        return jsonify({"ok": True, "step": step})

    @bp.route("/lesson/broadcast", methods=["POST"])
    def _broadcast():
        if not _verify_pin(bp.class_config):
            return jsonify({"error": "Unauthorized"}), 403
        d   = request.get_json(force=True, silent=True) or {}
        msg = str(d.get("message", ""))[:500]
        session_state.set_broadcast(class_id, msg)
        lesson_id = bp.class_config.get("lesson_id", class_id)
        current_app.mqtt.publish(f"{lesson_id}/control/broadcast", {"message": msg})
        sse.push(class_id, {"type": "broadcast", "message": msg})
        return jsonify({"ok": True})

    # ── Push a question to all devices via MQTT ──────────────────────────────

    @bp.route("/lesson/push-question", methods=["POST"])
    def _push_question():
        if not _verify_pin(bp.class_config):
            return jsonify({"error": "Unauthorized"}), 403
        data = request.get_json(force=True, silent=True) or {}
        q_index = data.get("index")
        if q_index is None:
            return jsonify({"error": "index required"}), 400

        active_ch = bp.class_config.get("active_lesson", "")
        questions = _load_questions(lessons_dir, active_ch)
        try:
            q_index = int(q_index)
        except (ValueError, TypeError):
            return jsonify({"error": "index must be integer"}), 400
        if q_index < 0 or q_index >= len(questions):
            return jsonify({"error": f"index {q_index} out of range"}), 400

        q = questions[q_index]
        lesson_id = bp.class_config.get("lesson_id", class_id)

        # Build MQTT payload matching firmware expectation
        mqtt_payload = {
            "lesson_id": q.get("id", f"q{q_index+1}"),
            "prompt": q.get("text", ""),
            "chapter": active_ch,
        }

        current_app.mqtt.publish(f"{lesson_id}/question", mqtt_payload)

        # Track which question is active + unlocked
        unlocked = session_state.unlock_step(class_id, q_index)
        sse.push(class_id, {
            "type": "question_pushed",
            "index": q_index,
            "question_id": q.get("id", f"q{q_index+1}"),
            "unlocked_steps": unlocked,
        })
        return jsonify({"ok": True, "index": q_index, "question_id": q.get("id"),
                         "unlocked_steps": unlocked})

    # ── Set active lesson chapter ─────────────────────────────────────────────

    @bp.route("/set-lesson", methods=["POST"])
    def _set_lesson():
        if not _verify_pin(bp.class_config):
            return jsonify({"error": "Unauthorized"}), 403
        data    = request.get_json(force=True)
        chapter = data.get("chapter", "").strip()
        if not chapter:
            return jsonify({"error": "chapter required"}), 400

        cfg_path = os.path.join(os.path.dirname(lessons_dir), "class_config.json")
        with open(cfg_path) as f:
            cfg = json.load(f)
        cfg["active_lesson"] = chapter
        with open(cfg_path, "w") as f:
            json.dump(cfg, f, indent=2)
        bp.class_config["active_lesson"] = chapter

        # Reset step state for new lesson
        session_state.reset_steps(class_id)
        sse.push(class_id, {"type": "lesson_changed", "chapter": chapter})
        return jsonify({"ok": True, "active_lesson": chapter})

    # ── Clear session ─────────────────────────────────────────────────────────

    @bp.route("/session/clear", methods=["POST"])
    def _clear_session():
        if not _verify_pin(bp.class_config):
            return jsonify({"error": "Unauthorized"}), 403
        session_state.clear(class_id)
        sse.push(class_id, {"type": "session_cleared"})
        return jsonify({"ok": True})

    # ── Device reset (wipe slot assignments) ──────────────────────────────────

    @bp.route("/devices/reset", methods=["POST"])
    def _devices_reset():
        if not _verify_pin(bp.class_config):
            return jsonify({"error": "Unauthorized"}), 403
        registry_reset(class_id)
        session_state.clear(class_id)
        sse.push(class_id, {"type": "devices_reset"})
        return jsonify({"ok": True})

    # ── Export downloads ──────────────────────────────────────────────────────

    @bp.route("/export/canvas")
    def _export_canvas():
        path = os.path.abspath(current_app.config.get(
            "CANVAS_EXPORT", "exports/canvas_grades.csv"
        ))
        if not os.path.isfile(path):
            return jsonify({"error": "No canvas export yet"}), 404
        return send_file(path, as_attachment=True, download_name="canvas_grades.csv")

    @bp.route("/export/ai")
    def _export_ai():
        path = os.path.abspath(current_app.config.get(
            "AI_EXPORT", "exports/ai_grading.json"
        ))
        if not os.path.isfile(path):
            return jsonify({"error": "No AI export yet"}), 404
        return send_file(path, as_attachment=True, download_name="ai_grading.json")

    # ── Reference code files ──────────────────────────────────────────────────

    @bp.route("/lesson/<chapter>/reference/<filename>")
    def _reference_file(chapter: str, filename: str):
        safe     = os.path.basename(filename)
        ref_path = os.path.join(lessons_dir, chapter, "reference", safe)
        if not os.path.isfile(ref_path):
            return jsonify({"error": f"Reference file '{safe}' not found"}), 404
        as_attachment = request.args.get("download", "0") == "1"
        ext      = os.path.splitext(safe)[1].lower()
        mimetype = "text/plain" if ext in {".ino", ".c", ".h", ".cpp", ".py", ".md"} \
                   else "application/octet-stream"
        return send_file(ref_path, mimetype=mimetype,
                         as_attachment=as_attachment, download_name=safe)

    # ── Admin: device mappings management ─────────────────────────────────────

    @bp.route("/admin/devices")
    def _admin_devices():
        if not _verify_pin(bp.class_config):
            pin = request.args.get("pin", "")
            if not pin:
                return render_template("admin_devices.html",
                                       class_id=class_id,
                                       class_name=bp.class_config.get("name", class_id),
                                       has_pin=True, need_pin=True)
        return render_template("admin_devices.html",
                               class_id=class_id,
                               class_name=bp.class_config.get("name", class_id),
                               has_pin=bool(bp.class_config.get("instructor_pin")),
                               need_pin=False)

    @bp.route("/admin/devices/api")
    def _admin_devices_api():
        if not _verify_pin(bp.class_config):
            return jsonify({"error": "Unauthorized"}), 403
        mappings = registry_get_all(class_id)
        devs    = device_state.get_all(class_id)
        # Enrich mappings with online status
        for m in mappings:
            ds = devs.get(str(m["slot"]), {})
            m["online"] = ds.get("online", False)
            m["student_id"] = ds.get("student_id", "")
            m["sw_us"] = ds.get("sw_us")
            m["hw_us"] = ds.get("hw_us")
            m["speedup"] = ds.get("speedup")
            # Flag suspicious MACs
            mac = m.get("mac", "")
            zeros = sum(1 for c in mac if c == '0')
            m["suspect"] = (mac.strip("0") == "") or (len(mac) >= 8 and zeros > len(mac) * 0.5)
        return jsonify({"mappings": mappings})

    @bp.route("/admin/devices/delete", methods=["POST"])
    def _admin_devices_delete():
        if not _verify_pin(bp.class_config):
            return jsonify({"error": "Unauthorized"}), 403
        data = request.get_json(force=True)
        mac  = data.get("mac", "")
        if not mac:
            return jsonify({"error": "mac required"}), 400
        ok = delete_by_mac(class_id, mac)
        if ok:
            sse.push(class_id, {"type": "device_mapping_deleted", "mac": mac})
        return jsonify({"ok": ok})


# ── Helper: load lesson steps for step-gated lessons ─────────────────────────

def _load_steps(lessons_dir: str, chapter: str) -> list:
    if not chapter:
        return []
    path = os.path.join(lessons_dir, chapter, "lesson.json")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("steps", [])
    # lesson.json is a list (question-only chapters) — no steps
    return []


def _load_questions(lessons_dir: str, chapter: str) -> list:
    """Load top-level questions from lesson.json (for question-push chapters)."""
    if not chapter:
        return []
    path = os.path.join(lessons_dir, chapter, "lesson.json")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("questions", [])
    return []
