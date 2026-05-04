"""
core/scoring_engine.py

Three-tier grading pipeline shared across all classes.

Tier 1 – Immediate keyword scoring   (instant, on submission)
Tier 2 – Canvas CSV export           (manual review / TA grading)
Tier 3 – AI grading JSON export      (async, for rich rubric feedback)

Each lesson's grading.json drives the rules; this engine is content-agnostic.

Grading.json schema:
{
  "max_points": 100,
  "questions": [
    {
      "id": "q1",
      "points": 20,
      "keywords": ["keyword1", "keyword2"],   // Tier 1: any match scores
      "keyword_mode": "any" | "all",          // default "any"
      "rubric": "Explain what the student should show"  // Tier 3
    }
  ]
}
"""
import csv
import json
import os
from datetime import datetime


# ── Tier 1: keyword scoring ──────────────────────────────────────────────────

def score_submission(answers: dict, grading_rules: dict) -> dict:
    """
    answers      = { "q1": "student answer text", ... }
    grading_rules = contents of grading.json

    Returns { "total": int, "max": int, "breakdown": { q_id: {"earned":, "max":, "matched": bool} } }
    """
    max_pts   = grading_rules.get("max_points", 100)
    questions = grading_rules.get("questions", [])
    breakdown = {}
    total     = 0

    for q in questions:
        q_id    = q.get("id") or q.get("question_id", "")
        q_pts   = q.get("points") or q.get("max_points", 0)
        answer  = str(answers.get(q_id, "")).lower()

        scoring = q.get("scoring", {})
        method  = scoring.get("method")

        if method == "keyword_weighted":
            # New schema: weighted required_concepts
            earned = 0
            for concept in scoring.get("required_concepts", []):
                if any(kw.lower() in answer for kw in concept.get("keywords_any", [])):
                    earned += concept.get("weight", 0)
            lp = scoring.get("length_penalty", {})
            if lp and len(answer.split()) < lp.get("under_word_count", 0):
                earned = max(0, earned - lp.get("penalty", 0))
            earned = min(earned, q_pts)
            matched = earned > 0
        else:
            # Legacy schema: flat keywords list
            keywords = [k.lower() for k in q.get("keywords", [])]
            mode     = q.get("keyword_mode", "any")
            if keywords:
                if mode == "all":
                    matched = all(kw in answer for kw in keywords)
                else:
                    matched = any(kw in answer for kw in keywords)
            else:
                matched = False
            earned = q_pts if matched else 0

        total += earned
        breakdown[q_id] = {"earned": earned, "max": q_pts, "matched": matched}

    return {"total": total, "max": max_pts, "breakdown": breakdown}


# ── Tier 2: Canvas CSV export ────────────────────────────────────────────────

def append_canvas_row(
    export_path: str,
    student_id: str,
    class_id: str,
    lesson_id: str,
    score: dict,
) -> None:
    """Appends one graded row to the Canvas CSV export."""
    os.makedirs(os.path.dirname(export_path), exist_ok=True)
    write_header = not os.path.isfile(export_path)
    with open(export_path, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["timestamp", "student_id", "class", "lesson", "score", "max", "pct"])
        pct = round(100 * score["total"] / score["max"]) if score["max"] else 0
        writer.writerow([
            datetime.utcnow().isoformat(),
            student_id, class_id, lesson_id,
            score["total"], score["max"], pct,
        ])


# ── Tier 3: AI grading JSON export ──────────────────────────────────────────

def append_ai_export(
    export_path: str,
    student_id: str,
    class_id: str,
    lesson_id: str,
    answers: dict,
    score: dict,
    grading_rules: dict,
) -> None:
    """
    Writes a JSON record suitable for feeding to an AI grading pipeline.
    Each record contains the full answer text + rubric so the AI has context.
    """
    os.makedirs(os.path.dirname(export_path), exist_ok=True)
    existing = []
    if os.path.isfile(export_path):
        with open(export_path) as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []

    rubrics = {
        (q.get("id") or q.get("question_id", "")): q.get("rubric") or q.get("grader_notes", "")
        for q in grading_rules.get("questions", [])
    }
    record  = {
        "timestamp":  datetime.utcnow().isoformat(),
        "student_id": student_id,
        "class":      class_id,
        "lesson":     lesson_id,
        "keyword_score": score,
        "responses": [
            {
                "question_id": q_id,
                "answer":      answers.get(q_id, ""),
                "rubric":      rubrics.get(q_id, ""),
            }
            for q_id in answers
        ],
    }
    existing.append(record)
    with open(export_path, "w") as f:
        json.dump(existing, f, indent=2)
