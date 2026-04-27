"""
core/session_state.py

In-memory store for the current class session.
Tracks: submissions, scores, lesson step state, broadcast message.
Resets on server restart (intentional – each class meeting is fresh).
"""
import threading
from collections import defaultdict

_lock = threading.Lock()

_submissions: dict[str, list[dict]]  = defaultdict(list)
_lesson_state: dict[str, dict]       = defaultdict(lambda: {
    "active_step":    0,
    "unlocked_steps": [0],
    "broadcast":      "",
    "scores":         {},
    "responses":      {},   # step_idx -> {slot -> {answer, correct, pts}}
})


# ── Submissions ───────────────────────────────────────────────────────────────

def record(class_id: str, entry: dict) -> None:
    with _lock:
        _submissions[class_id].append(entry)
        # Also record in step-response tracker if step info present
        step = entry.get("step")
        if step is not None:
            slot   = str(entry.get("slot", ""))
            answer = str(entry.get("answer", ""))
            pct    = entry.get("pct", 0)
            correct = entry.get("correct")
            pts     = entry.get("pts", 0)
            resp = _lesson_state[class_id]["responses"].setdefault(str(step), {})
            resp[slot] = {"answer": answer, "correct": correct, "pts": pts}
            # Update score
            sc = _lesson_state[class_id]["scores"].setdefault(slot, {"total": 0, "detail": {}})
            sc["detail"][str(step)] = {"pts": pts, "correct": correct}
            sc["total"] = sum(v.get("pts", 0) for v in sc["detail"].values())


def get_all(class_id: str) -> list[dict]:
    with _lock:
        return list(_submissions[class_id])


def clear(class_id: str) -> None:
    with _lock:
        _submissions[class_id].clear()
        _lesson_state[class_id] = {
            "active_step":    0,
            "unlocked_steps": [0],
            "broadcast":      "",
            "scores":         {},
            "responses":      {},
        }


def submitted_slots(class_id: str) -> set[int]:
    with _lock:
        return {e["slot"] for e in _submissions[class_id]}


# ── Lesson step state ─────────────────────────────────────────────────────────

def get_lesson_state(class_id: str) -> dict:
    with _lock:
        s = _lesson_state[class_id]
        return {
            "active_step":    s["active_step"],
            "unlocked_steps": list(s["unlocked_steps"]),
            "broadcast":      s["broadcast"],
            "response_counts": _build_response_counts(class_id),
        }


def unlock_step(class_id: str, step: int) -> list[int]:
    with _lock:
        unlocked = _lesson_state[class_id]["unlocked_steps"]
        if step not in unlocked:
            unlocked.append(step)
        _lesson_state[class_id]["active_step"] = step
        return list(unlocked)


def set_active_step(class_id: str, step: int) -> None:
    with _lock:
        _lesson_state[class_id]["active_step"] = step


def reset_steps(class_id: str) -> None:
    with _lock:
        _lesson_state[class_id]["active_step"]    = 0
        _lesson_state[class_id]["unlocked_steps"] = [0]
        _lesson_state[class_id]["responses"]      = {}
        _lesson_state[class_id]["scores"]         = {}


def set_broadcast(class_id: str, message: str) -> None:
    with _lock:
        _lesson_state[class_id]["broadcast"] = message


def get_scores(class_id: str) -> dict:
    with _lock:
        return dict(_lesson_state[class_id]["scores"])


def get_response_counts(class_id: str) -> dict:
    with _lock:
        return _build_response_counts(class_id)


def _build_response_counts(class_id: str) -> dict:
    resp   = _lesson_state[class_id].get("responses", {})
    counts = {}
    for step_str, sr in resp.items():
        n  = len(sr)
        nc = sum(1 for v in sr.values() if v.get("correct") is True)
        nw = sum(1 for v in sr.values() if v.get("correct") is False)
        counts[step_str] = {"responded": n, "correct": nc, "wrong": nw}
    return counts
