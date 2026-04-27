# Classroom Server

Flask + MQTT interactive lesson system for embedded systems courses.

\---

## Directory layout

```
classroom-server/
│
├── run.py                        # Entry point  →  python run.py
│
├── core/                         # Shared infrastructure (edit rarely)
│   ├── server.py                 # Flask app factory
│   ├── class\\\_loader.py           # Auto-discovers \\\& registers classes/
│   ├── mqtt\\\_manager.py           # MQTT broker connection + dispatch
│   ├── scoring\\\_engine.py         # Three-tier grading pipeline
│   ├── attendance.py             # Check-in + bonus tracking
│   └── config.py                 # Global settings (broker, ports, paths)
│
├── classes/                      # One sub-folder per course
│   ├── cecs346/
│   │   ├── class\\\_config.json     # Course metadata \\\& thresholds
│   │   ├── routes.py             # Flask Blueprint  (must export `bp`)
│   │   └── lessons/
│   │       ├── ch10/
│   │       │   ├── lesson.json   # Questions, title, objectives, diagram ref
│   │       │   └── grading.json  # Keyword rules, point values, AI rubrics
│   │       └── ch11/ … ch14/     # Same pattern for every chapter
│   │
│   └── cecs460/
│       ├── class\\\_config.json
│       ├── routes.py
│       └── lessons/
│           └── ch11/ … ch15/
│
├── templates/
│   └── lesson.html               # Shared Jinja2 template for all lessons
│
├── static/                       # CSS, JS, SVG diagrams
│
└── exports/                      # Auto-created at runtime
    ├── canvas\\\_grades.csv          # Tier 2 – Canvas import
    ├── ai\\\_grading.json            # Tier 3 – AI grading export
    └── attendance.json            # Per-session check-in log
```

\---

## Quick start

```bash
pip install flask paho-mqtt
python run.py
```

Visit `http://localhost:5000/` — returns registered classes.
Visit `http://localhost:5000/cecs346/lesson/ch10?slot=7` — lesson for slot 7.

\---

## API reference

|Method|URL|Description|
|-|-|-|
|GET|`/<class>/`|List available chapters + active lesson|
|GET|`/<class>/lesson/<ch>?slot=N`|Render lesson HTML for slot N|
|POST|`/<class>/submit/<ch>`|Score answers, write exports|
|GET|`/<class>/attendance/<ch>`|JSON attendance log for chapter|

**POST body** (`/submit/<ch>`):

```json
{
  "slot": 7,
  "student\\\_id": "slot\\\_7",
  "answers": {
    "q1": "student answer text",
    "q2": "another answer"
  }
}
```

\---

## Adding a new class

1. Create `classes/<new\\\_id>/`
2. Add `class\\\_config.json` (copy from cecs346 and edit)
3. Add `routes.py` (copy from cecs346/routes.py — only the Blueprint name needs changing)
4. Add `lessons/ch01/lesson.json` and `lessons/ch01/grading.json`

The server auto-discovers and registers the new class on next startup — **no edits to core/ required**.

\---

## Adding a lesson to an existing class

1. Create `classes/<class\\\_id>/lessons/<chXX>/`
2. Write `lesson.json` — see schema below
3. Write `grading.json` — see schema below
4. Set `"active\\\_lesson": "chXX"` in `class\\\_config.json`
5. Restart the server (or reload — no code changes needed)

### lesson.json schema

```jsonc
{
  "chapter": "ch10",
  "title": "Human-readable title",
  "learning\\\_objectives": \\\["obj 1", "obj 2"],
  "questions": \\\[
    {
      "id": "q1",                       // must match grading.json
      "text": "Question text {value}",  // {value} replaced per-slot
      "type": "short\\\_answer",
      "value\\\_pool": \\\["A", "B", "C"],    // optional; one picked per slot
      "value": "A"                      // default if no pool
    }
  ],
  "diagram": "filename.svg",            // null or filename in static/
  "references": \\\["Book §3.4"]
}
```

### grading.json schema

```jsonc
{
  "chapter": "ch10",
  "max\\\_points": 100,
  "questions": \\\[
    {
      "id": "q1",
      "points": 30,
      "keywords": \\\["term1", "term2"],   // Tier 1 keyword match
      "keyword\\\_mode": "any",            // "any" | "all"
      "rubric": "What a full answer looks like (used by AI grader)"
    }
  ]
}
```

\---

## Grading pipeline

|Tier|Trigger|Output|
|-|-|-|
|1 – Keyword|Immediate on submission|Score returned to ESP32|
|2 – Canvas|Every submission|`exports/canvas\\\_grades.csv`|
|3 – AI|Every submission|`exports/ai\\\_grading.json`|

Keyword scoring awards full points for a question if any (or all, depending on `keyword\\\_mode`) keywords appear in the student's answer.
Questions with an empty `keywords` list are marked 0 by keyword scoring and flagged for AI/manual review.

\---

## Configuration

Edit `core/config.py` for global defaults.
Override per-class by editing `class\\\_config.json` (`score\\\_pass\\\_pct`, `score\\\_bonus\\\_pct`, `active\\\_lesson`).

```python
MQTT\\\_BROKER   = "localhost"
MQTT\\\_PORT     = 1883
MQTT\\\_TOPIC    = "classroom/#"
CLASSES\\\_DIR   = "classes"
PASS\\\_SCORE    = 70       # percent
BONUS\\\_SCORE   = 90       # percent
CANVAS\\\_EXPORT = "exports/canvas\\\_grades.csv"
AI\\\_EXPORT     = "exports/ai\\\_grading.json"
```

