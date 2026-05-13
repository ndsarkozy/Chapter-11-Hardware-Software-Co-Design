"""
classes/cecs460/routes.py  –  CECS 460 System-on-Chip Design
URL prefix: /cecs460/

This version adds demo-mode support (Final Expo three-phase format) on top of
the existing dashboard, lesson, submit, and attendance routes, plus the
browser-login route used when a student is connecting from a laptop without
an ESP32 serial session (mirrors the /login handlers in cecs346 and cecs301).
"""
import hashlib
import json
import os
from datetime import datetime
from flask import (
    Blueprint, render_template, request, jsonify, redirect, current_app,
)
from core.scoring_engine import score_submission, append_canvas_row, append_ai_export
from core.attendance import record_checkin
from core import sse, session_state, device_state
from core.device_registry import allocate_slot, verify_token, lookup_by_slot
from core.dashboard_routes import register_dashboard_routes
from core.demo_routes import register_demo_routes  # NEW

bp          = Blueprint("cecs460", __name__)
LESSONS_DIR = os.path.join(os.path.dirname(__file__), "lessons")


def _name_to_mac(name: str) -> str:
    """Stable fake MAC from student name — same name always gets the same seat."""
    h = hashlib.sha256(name.strip().lower().encode("utf-8")).hexdigest()[:12]
    return h.upper()


# ── Browser login (for students without an ESP32 serial session) ──────────────
#
# The Student Login URL printed at server startup
# (http://<ip>:5000/cecs460/login) is rendered here. Pattern matches
# cecs346/routes.py and cecs301/routes.py.

@bp.route("/login", methods=["GET", "POST"])
def login():
    cfg    = bp.class_config
    active = cfg.get("active_lesson", "ch01")

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template(
                "login_460.html",
                class_name=cfg.get("name", "CECS 460"),
                error="Please enter your name.",
            )

        mac    = _name_to_mac(name)
        result = allocate_slot(
            "cecs460", mac, name,
            max_slots=cfg.get("slot_count", 30),
        )
        if result is None:
            return render_template(
                "login_460.html",
                class_name=cfg.get("name", "CECS 460"),
                error="Class is full — no seats available.",
            )

        slot  = result["slot"]
        token = result["token"]

        device_state.update("cecs460", str(slot), {
            "online": True, "student_id": name, "source": "browser",
        })
        sse.push("cecs460", {
            "type":       "device_status",
            "slot":       slot,
            "student_id": name,
            "online":     True,
        })

        return redirect(f"/cecs460/lesson/{active}?slot={slot}&token={token}")

    return render_template(
        "login_460.html",
        class_name=cfg.get("name", "CECS 460"),
        error=None,
    )


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


@bp.route("/")
def class_home():
    cfg = bp.class_config
    chapters = sorted(e.name for e in os.scandir(LESSONS_DIR)
                      if e.is_dir() and os.path.isfile(os.path.join(e.path, "lesson.json")))
    # Also surface chapters that have a demo.json
    demos = sorted(e.name for e in os.scandir(LESSONS_DIR)
                   if e.is_dir() and os.path.isfile(os.path.join(e.path, "demo.json")))
    return jsonify({
        "class":    cfg["name"],
        "chapters": chapters,
        "demos":    demos,
        "active":   cfg.get("active_lesson")
    })


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

    # Look up student display name for the device panel
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
    student = data.get("student_id", f"slot_{slot}")

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
                q = steps[int(step)].get("question", {})
                feedback = q.get("explanation", "")
                submitted = str(list(answers.values())[0]) if answers else ""
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


# Standard dashboards and demo routes.
register_dashboard_routes(bp, "cecs460", LESSONS_DIR)
register_demo_routes(bp, "cecs460", LESSONS_DIR)  # NEW
