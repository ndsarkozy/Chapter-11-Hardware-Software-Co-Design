"""
classes/cecs460/routes.py  –  CECS 460 System-on-Chip Design
URL prefix: /cecs460/
"""
import json
import os
import hashlib
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, current_app
from core.scoring_engine import score_submission, append_canvas_row, append_ai_export
from core.attendance import record_checkin
from core import sse, session_state
from core.device_registry import allocate_slot, verify_token, lookup_by_slot
from core.dashboard_routes import register_dashboard_routes

bp          = Blueprint("cecs460", __name__)
LESSONS_DIR = os.path.join(os.path.dirname(__file__), "lessons")


def _load_lesson(chapter):
    path = os.path.join(LESSONS_DIR, chapter, "lesson.json")
    return json.load(open(path, encoding="utf-8")) if os.path.isfile(path) else None

def _load_grading(chapter):
    path = os.path.join(LESSONS_DIR, chapter, "grading.json")
    return json.load(open(path, encoding="utf-8")) if os.path.isfile(path) else None

def _vary_for_slot(lesson, slot):
    import copy, random
    varied = copy.deepcopy(lesson)
    rng = random.Random(slot)
    for q in varied.get("questions", []):
        if "value_pool" in q:
            q["value"] = rng.choice(q["value_pool"])
    for step in varied.get("steps", []):
        q = step.get("question", {})
        if "value_pool" in q:
            q["value"] = rng.choice(q["value_pool"])
    return varied


def _name_to_mac(name: str) -> str:
    """Stable fake MAC from student name — same name always gets the same slot."""
    h = hashlib.sha256(name.strip().lower().encode("utf-8")).hexdigest()[:12]
    return h.upper()


# ── Browser login (same pattern as CECS 301) ─────────────────────────────────

@bp.route("/login", methods=["GET", "POST"])
def login():
    cfg = bp.class_config
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template("login_460.html",
                                   class_name=cfg.get("name", "CECS 460"),
                                   error="Please enter your name.")

        mac = _name_to_mac(name)
        result = allocate_slot("cecs460", mac, name,
                               max_slots=cfg.get("slot_count", 30))

        if result is None:
            return render_template("login_460.html",
                                   class_name=cfg.get("name", "CECS 460"),
                                   error="Class is full — no slots available.")

        slot  = result["slot"]
        token = result["token"]

        from core import device_state
        device_state.update("cecs460", str(slot), {
            "online": True, "student_id": name, "source": "browser",
        })
        sse.push("cecs460", {
            "type": "device_status",
            "slot": slot, "student_id": name, "online": True,
        })

        chapter = cfg.get("active_lesson", "ch11")
        return redirect(f"/cecs460/lesson/{chapter}?slot={slot}&token={token}")

    return render_template("login_460.html",
                           class_name=cfg.get("name", "CECS 460"),
                           error=None)


@bp.route("/")
def class_home():
    cfg = bp.class_config
    chapters = sorted(e.name for e in os.scandir(LESSONS_DIR)
                      if e.is_dir() and os.path.isfile(os.path.join(e.path, "lesson.json")))
    return jsonify({"class": cfg["name"], "chapters": chapters, "active": cfg.get("active_lesson")})


@bp.route("/lesson/<chapter>")
def lesson(chapter):
    slot  = request.args.get("slot", 0, type=int)
    token = request.args.get("token", "")
    fmt   = request.args.get("fmt", "html")

    raw = _load_lesson(chapter)
    if raw is None:
        return jsonify({"error": f"Lesson '{chapter}' not found"}), 404

    varied = _vary_for_slot(raw, slot)

    # Alias new-schema keys to legacy keys the template expects.
    # `chapter` MUST be the URL chapter (used by JS to build the submit URL),
    # NOT lesson.chapter_id which is a content slug.
    varied["chapter"] = chapter
    varied.setdefault("title", varied.get("chapter_title", chapter))

    if fmt == "json":
        return jsonify(varied)

    cfg = bp.class_config
    if cfg.get("instructor_pin") and token:
        if not verify_token("cecs460", slot, token):
            return render_template("access_denied.html", class_id="cecs460"), 403
    elif cfg.get("instructor_pin") and not token:
        return render_template("access_required.html", class_id="cecs460")

    reg = lookup_by_slot("cecs460", slot)
    student_name = (reg.get("device_id") or "").strip() if reg else ""
    return render_template("lesson.html", lesson=varied, chapter=chapter,
                           slot=slot, token=token, class_id="cecs460",
                           student_name=student_name,
                           server_ip=current_app.config.get("SERVER_IP", ""))


@bp.route("/submit/<chapter>", methods=["POST"])
def submit(chapter):
    data    = request.get_json(force=True)
    slot    = data.get("slot", 0)
    token   = data.get("token", "")
    answers = data.get("answers", {})
    step    = data.get("step")

    cfg = bp.class_config
    if cfg.get("instructor_pin"):
        if not verify_token("cecs460", slot, token):
            return jsonify({"error": "Unauthorized"}), 403

    grading = _load_grading(chapter)
    if grading is None:
        return jsonify({"error": f"Grading rules for '{chapter}' not found"}), 404

    score   = score_submission(answers, grading)
    pct     = score["total"] / score["max"] * 100 if score["max"] else 0
    bonus   = pct >= cfg.get("score_bonus_pct", 90)
    student = (data.get("student_id") or "").strip()
    if not student:
        reg = lookup_by_slot("cecs460", slot)
        student = (reg.get("device_id") or "").strip() if reg else ""
    if not student:
        student = f"slot_{slot}"

    append_canvas_row(current_app.config["CANVAS_EXPORT"], student, "cecs460", chapter, score)
    append_ai_export(current_app.config["AI_EXPORT"],     student, "cecs460", chapter, answers, score, grading)
    record_checkin(student, "cecs460", chapter, bonus=bonus)

    feedback = ""
    correct  = None
    pts      = score["total"]
    if step is not None:
        raw = _load_lesson(chapter)
        if raw:
            steps = raw.get("steps", [])
            if 0 <= int(step) < len(steps):
                step_obj = steps[int(step)]
                submitted = str(list(answers.values())[0]) if answers else ""
                q_id_submitted = list(answers.keys())[0] if answers else ""

                # Support both schemas:
                # Old schema: step.question  with q_id / type / correct / explanation
                # Our schema: step.short_answer_prompt  with question_id
                q = step_obj.get("question", {})
                sap = step_obj.get("short_answer_prompt", {})

                # Determine effective question id and type
                if sap:
                    q_id   = sap.get("question_id", q_id_submitted)
                    q_type = "free_response"
                else:
                    q_id   = q.get("q_id", q_id_submitted)
                    q_type = q.get("type", "mc")

                feedback = q.get("explanation", "")

                if q_type in ("free_response", "hw_result"):
                    # Find matching grading question — support both "id" and "question_id" keys
                    grading_q = next(
                        (gq for gq in grading.get("questions", [])
                         if gq.get("question_id") == q_id or gq.get("id") == q_id),
                        None
                    )
                    if grading_q:
                        ans_lower = submitted.lower()
                        max_pts   = grading_q.get("max_points", grading_q.get("points", 10))

                        # Our schema uses required_concepts / keyword_weighted
                        if grading_q.get("scoring", {}).get("method") == "keyword_weighted":
                            awarded = 0
                            for concept in grading_q["scoring"].get("required_concepts", []):
                                if any(kw.lower() in ans_lower for kw in concept.get("keywords_any", [])):
                                    awarded += concept.get("weight", 0)
                            # Length penalty
                            lp = grading_q["scoring"].get("length_penalty", {})
                            if lp and len(submitted.split()) < lp.get("under_word_count", 0):
                                awarded = max(0, awarded - lp.get("penalty", 0))
                            pts = min(awarded, max_pts)
                        else:
                            # Old schema: flat keywords list
                            kws     = grading_q.get("keywords", [])
                            matched = sum(1 for kw in kws if kw.lower() in ans_lower)
                            ratio   = matched / len(kws) if kws else 0
                            pts     = min(round(ratio * max_pts), max_pts)

                        correct = pts > 0
                        pct     = round(pts / max_pts * 100) if max_pts else 0
                        feedback = grading_q.get("grader_notes", grading_q.get("rubric", ""))
                    else:
                        pts = 5  # partial credit — no matching rubric found
                        correct = True
                        pct = 50
                else:
                    # MC / TF: exact match
                    correct_ans = str(q.get("correct", ""))
                    correct = submitted.strip().lower() == correct_ans.strip().lower()
                    pts = 10 if correct else 0
                    pct = 100 if correct else 0

                bonus = False   # bonus evaluated on full lesson, not per step

    entry = {
        "type":      "submission",
        "slot":      slot,
        "student":   student,
        "chapter":   chapter,
        "score":     score,
        "pct":       round(pct),
        "bonus":     bonus,
        "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
        "source":    "http",
        "step":      step,
        "correct":   correct,
        "pts":       pts,
    }
    session_state.record("cecs460", entry)
    sse.push("cecs460", entry)

    return jsonify({"ok": True, "score": score, "bonus": bonus,
                    "pct": round(pct), "correct": correct,
                    "pts": pts, "feedback": feedback})


@bp.route("/attendance/<chapter>")
def attendance(chapter):
    from core.attendance import get_attendance
    return jsonify(get_attendance(class_id="cecs460", lesson_id=chapter))


# ── Link browser session to an ESP32 device slot ─────────────────────────────

@bp.route("/link-device", methods=["POST"])
def link_device():
    """
    Student provides their ESP32's slot number. The browser session adopts
    the ESP32's slot + token, so bench telemetry and browser answers share
    one identity on the dashboard.
    """
    data = request.get_json(force=True)
    esp_slot = data.get("esp_slot")
    if esp_slot is None:
        return jsonify({"error": "esp_slot required"}), 400

    try:
        esp_slot = int(esp_slot)
    except (ValueError, TypeError):
        return jsonify({"error": "esp_slot must be a number"}), 400

    # Find the ESP32's mapping entry
    esp_entry = lookup_by_slot("cecs460", esp_slot)
    if esp_entry is None:
        return jsonify({"error": f"No ESP32 registered at slot {esp_slot}"}), 404

    # Return the ESP32's slot + token so the browser can adopt them
    return jsonify({
        "ok": True,
        "slot": esp_entry["slot"],
        "token": esp_entry["token"],
    })


@bp.route("/api/devices")
def api_devices():
    """Return list of ESP32-assigned slots (for the link-device UI)."""
    from core import device_state
    devs = device_state.get_all("cecs460")
    # Only show ESP32 devices (those with real MAC, not browser name-hash)
    esp_devices = []
    for sid, dev in devs.items():
        if dev.get("source") != "browser" and dev.get("online"):
            esp_devices.append({
                "slot": dev.get("slot", sid),
                "device_id": dev.get("device_id", ""),
                "mac": dev.get("mac", ""),
            })
    return jsonify({"devices": esp_devices})


register_dashboard_routes(bp, "cecs460", LESSONS_DIR)
