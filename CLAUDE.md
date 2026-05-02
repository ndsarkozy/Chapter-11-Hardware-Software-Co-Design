# CECS 460 — Chapter 11 Module

## What this is

Final project for CECS 460 (System on Chip) at CSULB, Spring 2026, by Nathan Sarkozy. An interactive classroom module for Chapter 11: Hardware/Software Co-Design. Students learn hardware/software partitioning by watching software fail under CPU load on an ESP32, then fixing it with the DMA controller.

Plugs into the ClassroomFusion server system — the full server lives at `repo/classroom-server/`.

## Repo layout

```
repo/
  classroom-server/           # Full ClassroomFusion server (run this to host the lesson)
    run.py                    # Entry point — starts MQTT broker + Flask server
    requirements.txt
    core/                     # UI engine: server, dashboard, MQTT, scoring, SSE
    classes/cecs460/
      class_config.json       # active_lesson: "ch11Final", lesson_id: "c460_ch11_codesign"
      lessons/ch11Final/      # lesson.json + grading.json the server actually loads at runtime
      routes.py
    templates/                # HTML templates for lesson, instructor, projector views
    tools/student_client.py   # Served at /tools/ — auto-detects ESP32, opens lesson page
    student_connect.bat       # Launcher for student_client.py
  hardware/
    starter_code/             # Arduino sketches students flash, one per step
      step1_baseline/         # LED blink, prints period+freq to Serial Monitor
      step2_overload/         # Pot + LCD + CPU load → LCD lags
      step4_accelerator/      # Same hardware + load, ADC via DMA → LCD smooth
      README.md               # Build/flash guide, wiring tables, common issues
    solution_code/
      CECS460_Lab11_AES/      # Professor's AES benchmark firmware (reference, don't give to students)
    BOM.md
  docs/
    instructor_guide.md       # Complete — deployment steps, per-step notes, grading workflow
    final_report.md           # Complete draft — design decisions, files created, recommendations
    contribution_statement.md # Template — fill in name before submission
  lesson_package/             # Submission artifact — copy into ch11Final before demo
    lesson.json               # All 5 steps fully built
    grading.json              # All 5 questions with keyword rubrics (tested)
    assets/
      step1_wiring.svg        # Step 1 wiring diagram (exists)
      step2_wiring.png        # MISSING — needs to be created
    instructor_notes/
      step1.md                # Instructor notes for Step 1
  lab/                        # Student-facing handouts
    step1_handout.md          # Complete
    step2_handout.md          # Complete
    step3_handout.md          # Complete
    step4_handout.md          # Complete
    step5_handout.md          # Complete
  testing_evidence/           # EMPTY — needs screenshots once hardware is tested
    README.md                 # Lists what evidence is expected
  tests/
    test_grading.py           # Tests all 5 rubric questions (35 cases, all passing)
  START_SERVER.bat
  STOP_SERVER.bat
  CHANGE_IP.bat
```

## 5-step lesson status

| Step | Title | lesson.json | grading.json | lab handout | firmware |
|------|-------|:-----------:|:------------:|:-----------:|:--------:|
| 1 | A blink that almost works | ✅ | ✅ q1 | ✅ | ✅ |
| 2 | Software under pressure | ✅ | ✅ q2 | ✅ | ✅ |
| 3 | Why did it fail? | ✅ | ✅ q3 | ✅ | (uses step2 fw) |
| 4 | The accelerator | ✅ | ✅ q4 | ✅ | ✅ |
| 5 | The partition decision | ✅ | ✅ q5 | ✅ | (no firmware) |

**All lesson content is written. All grading rubrics pass automated tests.**

## Lesson concept (Steps 2–4)

- **Hardware:** Potentiometer on GPIO 34 + 16×2 LCD (I2C, GPIO 21/22)
- **Step 2 failure:** CPU polls ADC in `analogRead()` loop while floating-point load task runs → LCD lags visibly behind knob; Serial Monitor shows sample rate ~40–80 Hz
- **Step 3 diagnose:** Students read sample rate from Serial Monitor, compare to a hypothetical 50 Hz requirement
- **Step 4 fix:** Reflash with `step4_accelerator.ino` — same hardware, ADC now via I2S DMA at 10 kHz → LCD smooth; Serial Monitor shows ~400–500 Hz
- **Hardware offload used:** ESP32 DMA controller via I2S ADC mode (no external hardware)
- **No WS2812 strip** — the LCD is the visual output (simpler wiring, same concept)
- **No oscilloscope** — all measurement via Serial Monitor

## Hardware (actual, per team)

- ESP32 DevKit (38-pin)
- Standard LED + 330 Ω resistor (step 1 only)
- Potentiometer 10 kΩ (steps 2–4, GPIO 34)
- 16×2 LCD with I2C backpack at address 0x27 (steps 2–4, SDA=GPIO21, SCL=GPIO22)
- USB data cable (not charge-only)

Full BOM: `repo/hardware/BOM.md`

## Network / server setup

- **Mango GL.iNet router** — local classroom network
- WiFi SSID: `DEEZ`, Password: `password`
- Laptop connects via Ethernet to Mango → IP `192.168.8.228`
- ESP32 connects to `DEEZ` WiFi → reaches MQTT broker at `192.168.8.228:1883`
- Server runs at `http://192.168.8.228:5000`
- Instructor dashboard: `http://192.168.8.228:5000/cecs460/instructor` (PIN: 4600)
- Student login: `http://192.168.8.228:5000/cecs460/login`

**Note:** `192.168.8.228` is DHCP — may change. Run `ipconfig` to verify.

## Starting the server

```bash
START_SERVER.bat        # Windows — double-click or run from terminal
# OR
cd repo/classroom-server && python run.py
```

## Key commands

```bash
# Validate grading rubric against sample answers (run before any grading.json changes)
python3 repo/tests/test_grading.py

# Start the classroom server
START_SERVER.bat
```

## What still needs to be done

### Must complete before submission

| Item | Notes |
|------|-------|
| **Sync `ch11Final` with `lesson_package/`** | Copy our lesson.json + grading.json into `classroom-server/classes/cecs460/lessons/ch11Final/` — server currently runs old AES lesson |
| **MQTT pass reporting in firmware** | Starter firmware (steps 2–4) doesn't send a pass signal to the server yet. Solution firmware does (AES benchmark). Spec requires server-triggered pass, not manual. |
| **Testing evidence** | Flash each sketch, screenshot Serial Monitor output, screenshot instructor dashboard showing a pass. Save to `testing_evidence/`. |
| **`assets/step2_wiring.png`** | Referenced in lesson.json step 2 but file doesn't exist. Create wiring diagram. |
| **Contribution statement** | Fill in name in `docs/contribution_statement.md`. |
| **Recorded demo video (5–10 min)** | Walk through from student + instructor perspective, show server pass. |
| **Expo slides** | Presentation outline for live demo. |

### Nice to have

| Item | Notes |
|------|-------|
| Instructor notes for steps 2–5 | Only step1.md exists in `lesson_package/instructor_notes/` |
| Step2 wiring asset | `assets/step2_wiring.png` missing — lesson.json references it |

## Critical known issue

`classroom-server/classes/cecs460/lessons/ch11Final/lesson.json` is the **old AES benchmark lesson** — it is what the server actually serves right now. Our new hands-on lesson lives in `lesson_package/`. Before testing the full loop (student → lesson → MQTT pass → dashboard), copy `lesson_package/lesson.json` and `lesson_package/grading.json` into `ch11Final/`.

## Professor's reference firmware

`repo/hardware/solution_code/CECS460_Lab11_AES/CECS460_Lab11_AES.ino` — professor's AES benchmark firmware. This is the only firmware that currently does MQTT pass reporting. Do not distribute to students — it's instructor-only reference.
