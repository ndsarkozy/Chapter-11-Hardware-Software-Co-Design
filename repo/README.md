# CECS 460 — Chapter 11: Hardware/Software Co-Design

An interactive classroom module that teaches hardware/software co-design by having students *do* it — watch software break under load, then rescue it with a dedicated hardware peripheral on the ESP32.

Built for the CECS 460 Interactive Classroom System at CSULB. Designed to be dropped into the system's chapter content directory and run with minimal instructor setup.

## What's in this module

Students spend ~2 hours working through 5 hands-on steps:

1. **A blink that almost works** — measure a software-timed 1 Hz signal and notice it isn't exactly 1 Hz
2. **Software under pressure** — scale up the task and watch software visibly fail
3. **Why did it fail?** — diagnose the cause from scope captures and CPU load data
4. **The accelerator** — swap to a dedicated hardware peripheral, rerun the same stress test, watch it succeed
5. **The partition decision** — fill in a decision matrix and recommend an implementation for a hypothetical product

By the end, students have *felt* the tradeoff co-design is about, not just read about it.

## Hardware students will wire, measure, and debug

- ESP32 DevKit
- Standard LED + 330 Ω resistor (step 1)
- 16-pixel WS2812 addressable LED strip + 470 Ω + 1000 μF capacitor (steps 2–5)
- Pushbutton + pull-down resistor (step 2 background-load task)
- Oscilloscope (2 channels, 20 MHz or better)

A full bill of materials is in [`hardware/BOM.md`](hardware/BOM.md).

## Repo layout

```
.
├── lesson_package/      # Files the classroom system loads
│   ├── lesson.json      # Step flow, content, interactive moments
│   ├── grading.json     # Scoring rubrics for short-answer questions
│   ├── assets/          # Diagrams, reference figures
│   └── instructor_notes/  # Per-step guidance for the instructor
├── lab/                 # Student-facing paper handouts (one per step)
├── hardware/
│   ├── starter_code/    # Sketches students flash, organized by step
│   ├── solution_code/   # Reference implementations for the instructor
│   └── BOM.md           # Bill of materials
├── docs/
│   ├── instructor_guide.md     # Overall deployment guide (1-2 pages)
│   ├── final_report.md         # Design decisions, testing, recommendations
│   └── contribution_statement.md
├── testing_evidence/    # Scope captures, grading test output, screenshots
├── tests/               # Automated checks for the grading rubric
└── .github/             # Issue templates and contribution guide
```

## For the instructor deploying next semester

Read [`docs/instructor_guide.md`](docs/instructor_guide.md) first. It covers what changed, why, required materials, setup, and expected trouble spots.

The short version:

```bash
# From the classroom system root
cp -r path/to/this/repo/lesson_package chapters/ch11/
```

Then restart the classroom system. Chapter 11 appears in the chapter list.

## For students

Read [`lab/step1_handout.md`](lab/step1_handout.md) first. Each step has its own handout.

## For developers maintaining this module

Run the grading tests before pushing any changes to `grading.json`:

```bash
python3 tests/test_grading.py
```

All test cases should pass. If you add or modify a scoring concept, add a test case that exercises it.

## Status

| Component | Status |
|---|---|
| Step 1 — A blink that almost works | Complete |
| Step 2 — Software under pressure | Not started |
| Step 3 — Why did it fail? | Not started |
| Step 4 — The accelerator | Not started |
| Step 5 — The partition decision | Not started |
| Instructor guide | In progress |
| Final report | Not started |

## License

MIT — see [LICENSE](LICENSE).

## Author

[Your Name], CECS 460, CSULB, Spring 2026.
