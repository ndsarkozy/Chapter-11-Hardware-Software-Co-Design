"""
core/attendance.py

Records which student slots checked in during a session, with optional
bonus flag for high scorers.  Writes to a simple JSON log.
"""
import json
import os
from datetime import datetime

ATTENDANCE_LOG = "exports/attendance.json"


def record_checkin(student_id: str, class_id: str, lesson_id: str, bonus: bool = False) -> None:
    os.makedirs(os.path.dirname(ATTENDANCE_LOG), exist_ok=True)
    existing = []
    if os.path.isfile(ATTENDANCE_LOG):
        with open(ATTENDANCE_LOG) as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []

    existing.append({
        "timestamp":  datetime.utcnow().isoformat(),
        "student_id": student_id,
        "class":      class_id,
        "lesson":     lesson_id,
        "bonus":      bonus,
    })
    with open(ATTENDANCE_LOG, "w") as f:
        json.dump(existing, f, indent=2)


def get_attendance(class_id: str | None = None, lesson_id: str | None = None) -> list[dict]:
    if not os.path.isfile(ATTENDANCE_LOG):
        return []
    with open(ATTENDANCE_LOG) as f:
        try:
            records = json.load(f)
        except json.JSONDecodeError:
            return []
    if class_id:
        records = [r for r in records if r.get("class") == class_id]
    if lesson_id:
        records = [r for r in records if r.get("lesson") == lesson_id]
    return records
