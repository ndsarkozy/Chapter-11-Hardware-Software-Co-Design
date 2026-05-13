# CECS 460 — Chapter 11: Hardware/Software Co-Design

An interactive classroom module that teaches hardware/software co-design by having students *do* it — watch software fail under CPU load, then rescue it with the ESP32's DMA controller.

Built for the CECS 460 Interactive Classroom System at CSULB. Drop-in compatible: the lesson content layer plugs into the existing classroom server with no engine rewrites.

## What's in this module

Students spend ~90 minutes working through 5 hands-on steps:

1. **A blink that almost works** — flash a 1 Hz blink, measure it on Serial Monitor, notice it isn't exactly 1 Hz
2. **Software under pressure** — add a potentiometer + LCD with a CPU load task; watch the LCD lag visibly behind the knob
3. **Why did it fail?** — read the live ADC sample rate from Serial Monitor; quantify the failure
4. **The accelerator** — flip `USE_DMA` from 0 to 1, reflash, watch the same load now sample at ~10× the rate; firmware auto-reports the pass to the server over MQTT
5. **The partition decision** — fill in a decision matrix and write a partitioning rule using the student's own measured numbers

By the end, students have *felt* the tradeoff co-design is about, not just read about it.

## Hardware students will wire (per team)

- ESP32 DevKit (38-pin, ESP-WROOM-32)
- Standard LED + 330 Ω resistor (step 1)
- 10 kΩ potentiometer (steps 2–4, GPIO 34)
- 16×2 LCD with I2C backpack at 0x27 (steps 2–4, SDA=GPIO21, SCL=GPIO22)
- USB **data** cable (not charge-only)

No oscilloscope required — all measurement is via Arduino IDE Serial Monitor at 115200 baud. Full bill of materials in [`hardware/BOM.md`](hardware/BOM.md).

## Repo layout

```
.
├── lesson_package/        # Files the classroom system loads
│   ├── lesson.json        # 5-step flow, interactive moments, reveals
│   ├── grading.json       # Keyword-weighted rubrics for q1–q5
│   ├── assets/            # Wiring diagrams (SVG)
│   └── instructor_notes/  # Per-step guidance for the instructor
├── lab/                   # Student handouts (one per step)
├── hardware/
│   ├── starter_code/      # Sketches students flash, one per step
│   │   ├── step1_baseline/      # 1 Hz blink + Serial Monitor period output
│   │   ├── step2_overload/      # Pot + LCD + CPU load (visible lag)
│   │   └── step4_accelerator/   # Same hardware, ADC via DMA + MQTT pass
│   ├── solution_code/     # Reference implementations (instructor only)
│   └── BOM.md
├── classroom-server/      # ClassroomFusion server (host the lesson here)
├── docs/
│   ├── instructor_guide.md
│   ├── final_report.md
│   ├── contribution_statement.md
│   └── expo_slides_outline.md
├── testing_evidence/      # End-to-end test screenshots and logs
├── tests/                 # test_grading.py — automated rubric tests
├── START_SERVER.bat       # Boot the classroom server
├── DEMO_MODE.bat          # One-click expo demo launcher
└── presentation.html      # Standalone slide deck for the live expo
```

## Quick start — running the module

```bat
:: Windows
START_SERVER.bat
```

Then open the instructor dashboard at `http://<server-ip>:5000/cecs460/instructor` (PIN: 4600).

For the live expo demo:

```bat
DEMO_MODE.bat
```

This boots the server, resets session state, and opens the presentation deck, projector view, and instructor dashboard side-by-side.

## For the instructor deploying next semester

Read [`docs/instructor_guide.md`](docs/instructor_guide.md) first. It covers what changed, why, required materials, classroom setup, and expected trouble spots.

The short version: copy `lesson_package/lesson.json` and `lesson_package/grading.json` into `classroom-server/classes/cecs460/lessons/ch11/`, set `active_lesson` to `ch11` in `class_config.json`, and start the server.

## For students

Read [`lab/step1_handout.md`](lab/step1_handout.md) first. Each step has its own handout.

## For developers maintaining this module

Run the grading tests before pushing any changes to `grading.json`:

```bash
python3 tests/test_grading.py
```

All 35 test cases should pass. If you add or modify a scoring concept, add a test case that exercises it.

## Status

| Component | Status |
|---|---|
| Step 1 — A blink that almost works | Complete |
| Step 2 — Software under pressure | Complete |
| Step 3 — Why did it fail? | Complete (reuses Step 2 firmware) |
| Step 4 — The accelerator | Complete (USE_DMA task + MQTT pass) |
| Step 5 — The partition decision | Complete |
| Grading rubric (35 automated tests) | Complete, all passing |
| Instructor guide | Complete |
| Final report | Complete (markdown — export to PDF before submission) |
| Contribution statement | Complete |
| Expo presentation deck | Complete (`presentation.html`) |
| Demo mode launcher | Complete (`DEMO_MODE.bat`) |
| Recorded demo video | Pending |
| End-to-end testing evidence | Pending — needs hardware run |

## License

MIT — see [LICENSE](LICENSE).

## Authors

Nathan Sarkozy and Christian Vanegas, CECS 460, CSULB, Spring 2026.
