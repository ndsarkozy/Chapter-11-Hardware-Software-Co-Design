# Contribution Statement

**Team:** Nathan Sarkozy and Christian Vanegas
**Chapter:** 11 — Hardware/Software Co-Design and Design Flow
**Course:** CECS 460, Spring 2026

Both team members contributed across all phases. The breakdown below identifies the primary owner for each area; both members reviewed and signed off on every deliverable.

| Area | Primary owner | Notes |
|---|---|---|
| Content design (lesson flow, pedagogy, step arc) | Nathan Sarkozy | Designed the "overwhelm → diagnose → rescue → generalize" structure; drafted opening lines, prose blocks, and reveals |
| Hardware implementation (wiring, sketches, DMA path) | Nathan Sarkozy | Wrote `step1_baseline.ino`, `step2_overload.ino`, `step4_accelerator.ino` including I2S/ADC DMA setup |
| Server integration (MQTT pass, slot/token handshake, scoring fix) | Christian Vanegas | Implemented `publishPass()`, `maintainNetwork()`, `mqttCallback()`; patched `core/scoring_engine.py` for the dual-schema grading; authored `ch11Lab/grading.json` |
| Assessment & grading rubric | Nathan Sarkozy | Authored all 5 keyword-weighted rubrics with exemplars and disqualifiers |
| Testing (rubric automation, end-to-end hardware) | Christian Vanegas | Wrote `tests/test_grading.py` (35 cases); ran the full firmware-flash → server-pass loop on physical hardware and captured testing evidence |
| Documentation (instructor guide, handouts, BOM) | Nathan Sarkozy | Wrote `docs/instructor_guide.md`, `lab/step{1-5}_handout.md`, and `lesson_package/instructor_notes/` |
| Final report | Both | Nathan drafted §1–§4 (summary, design decisions, hardware); Christian drafted §5–§6 (testing process, recommendations) |
| Presentation & demo (slides, video, expo run) | Both | Christian led the live expo demo (firmware flash + server pass on stage); Nathan handled the slides, narration, and recorded walkthrough video |

## AI tool usage disclosure

AI assistants (Claude) were used for ideation, drafting content, structural review, and code review. Every pedagogical decision, hardware partition choice, grading rubric, wiring diagram, and measurement was made and verified by the team. All hardware was wired, flashed, and tested by us; all testing evidence in `testing_evidence/` is from our own measurements on the classroom ESP32.
