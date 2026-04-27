# CECS 460 — Chapter 11 Module

## What this is

Final project for CECS 460 (System on Chip) at CSULB, Spring 2026, by Nathan Sarkozy. An interactive classroom module for Chapter 11: Hardware/Software Co-Design. Students learn hardware/software partitioning by watching software fail under load on an ESP32, then fixing it with a dedicated hardware peripheral.

Plugs into CSULB's Interactive Classroom System by copying `lesson_package/` into `chapters/ch11/`.

## Repo layout

```
lesson_package/         # What the classroom system loads
  lesson.json           # Step flow, content, interactive moments
  grading.json          # Scoring rubrics
  assets/               # Diagrams, reference figures
  instructor_notes/     # Per-step instructor guidance
lab/                    # Student-facing handouts (one per step)
hardware/
  starter_code/         # Arduino sketches students flash, by step
  solution_code/        # Reference implementations (instructor only)
  BOM.md                # Bill of materials
docs/
  instructor_guide.md
  final_report.md
  contribution_statement.md
testing_evidence/       # Scope captures, screenshots, grading test output
tests/
  test_grading.py       # Automated checks for grading.json rubric
```

## 5-step lesson (~2 hours)

| Step | Title | Status |
|------|-------|--------|
| 1 | A blink that almost works — measure software-timed 1 Hz signal, notice drift | Complete |
| 2 | Software under pressure — scale up, watch software fail | Not started |
| 3 | Why did it fail? — diagnose via scope + CPU load data | Not started |
| 4 | The accelerator — swap to hardware peripheral, rerun stress test | Not started |
| 5 | The partition decision — fill in decision matrix | Not started |

Instructor guide: in progress. Final report: not started.

## Hardware

- ESP32 DevKit
- Standard LED + 330 Ω resistor (step 1)
- 16-pixel WS2812 addressable LED strip + 470 Ω resistor + 1000 µF capacitor (steps 2–5)
- Pushbutton + 10 kΩ pull-down resistor
- Oscilloscope (2 channels, 20 MHz or better)

Full BOM: `hardware/BOM.md`

## Key commands

```bash
# Run grading rubric tests before pushing changes to grading.json
python3 tests/test_grading.py
```
