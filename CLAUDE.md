# CECS 460 â€” Chapter 11 Module

## What this is

Final project for CECS 460 (System on Chip) at CSULB, Spring 2026, by **Nathan Sarkozy and Christian Vanegas** (two-person team). An interactive classroom module for Chapter 11: Hardware/Software Co-Design. Students learn hardware/software partitioning by watching software fail under CPU load on an ESP32, then fixing it with the DMA controller.

Plugs into the ClassroomFusion server system â€” the full server lives at `repo/classroom-server/`.

## Repo layout

```
repo/
  classroom-server/           # Full ClassroomFusion server (run this to host the lesson)
    run.py                    # Entry point â€” starts MQTT broker + Flask server
    requirements.txt
    core/                     # UI engine: server, dashboard, MQTT, scoring, SSE
    classes/cecs460/
      class_config.json       # active_lesson: "ch11Final", lesson_id: "c460_ch11_codesign"
      lessons/ch11Final/      # lesson.json + grading.json the server actually loads at runtime
      routes.py
    templates/                # HTML templates for lesson, instructor, projector views
    tools/student_client.py   # Served at /tools/ â€” auto-detects ESP32, opens lesson page
    student_connect.bat       # Launcher for student_client.py
  hardware/
    starter_code/             # Arduino sketches students flash, one per step
      step1_baseline/         # LED blink, prints period+freq to Serial Monitor
      step2_overload/         # Pot + LCD + CPU load â†’ LCD lags
      step4_accelerator/      # Same hardware + load, ADC via DMA â†’ LCD smooth
      README.md               # Build/flash guide, wiring tables, common issues
    solution_code/
      CECS460_Lab11_AES/      # Professor's AES benchmark firmware (reference, don't give to students)
    BOM.md
  docs/
    instructor_guide.md       # Complete â€” deployment steps, per-step notes, grading workflow
    final_report.md           # Complete draft â€” design decisions, files created, recommendations
    contribution_statement.md # Nathan Sarkozy (filled in)
    expo_slides_outline.md    # Expo presentation outline (10 slides)
  lesson_package/             # Submission artifact â€” copy into ch11Final before demo
    lesson.json               # All 5 steps fully built
    grading.json              # All 5 questions with keyword rubrics (tested)
    assets/
      step1_wiring.svg        # Step 1 wiring diagram
      step2_wiring.svg        # Steps 2-4 wiring diagram (LCD + pot)
    instructor_notes/
      step1.md through step5.md  # Instructor notes for all steps
  lab/                        # Student-facing handouts
    step1_handout.md          # Complete
    step2_handout.md          # Complete
    step3_handout.md          # Complete
    step4_handout.md          # Complete
    step5_handout.md          # Complete
  testing_evidence/           # EMPTY â€” needs screenshots once hardware is tested
    README.md                 # Lists what evidence is expected
  tests/
    test_grading.py           # Tests all 5 rubric questions (35 cases, all passing)
  START_SERVER.bat
  STOP_SERVER.bat
  CHANGE_IP.bat
  DEMO_MODE.bat              # Expo demo launcher â€” starts server, opens presentation + dashboard + projector
  presentation.html          # Standalone slide deck for the live expo (arrow keys + S/D/F shortcuts)
```

## 5-step lesson status

| Step | Title | lesson.json | grading.json | lab handout | firmware |
|------|-------|:-----------:|:------------:|:-----------:|:--------:|
| 1 | A blink that almost works | âœ… | âœ… q1 | âœ… | âœ… |
| 2 | Software under pressure | âœ… | âœ… q2 | âœ… | âœ… |
| 3 | Why did it fail? | âœ… | âœ… q3 | âœ… | (uses step2 fw) |
| 4 | The accelerator | âœ… | âœ… q4 | âœ… | âœ… + MQTT pass |
| 5 | The partition decision | âœ… | âœ… q5 | âœ… | (no firmware) |

**All lesson content is written. All grading rubrics pass automated tests.**

## Lesson concept (Steps 2â€“4)

- **Hardware:** Potentiometer on GPIO 34 + 16Ã—2 LCD (I2C, GPIO 21/22)
- **Step 2 failure:** CPU polls ADC in `analogRead()` loop while floating-point load task runs â†’ LCD lags visibly behind knob; Serial Monitor shows sample rate ~40â€“80 Hz
- **Step 3 diagnose:** Students read sample rate from Serial Monitor, compare to a hypothetical 50 Hz requirement
- **Step 4 fix:** Reflash with `step4_accelerator.ino` â€” same hardware, ADC now via I2S DMA at 10 kHz â†’ LCD smooth; Serial Monitor shows ~400â€“500 Hz
- **Hardware offload used:** ESP32 DMA controller via I2S ADC mode (no external hardware)
- **No WS2812 strip** â€” the LCD is the visual output (simpler wiring, same concept)
- **No oscilloscope** â€” all measurement via Serial Monitor

## Hardware (actual, per team)

- ESP32 DevKit (38-pin)
- Standard LED + 330 Î© resistor (step 1 only)
- Potentiometer 10 kÎ© (steps 2â€“4, GPIO 34)
- 16Ã—2 LCD with I2C backpack at address 0x27 (steps 2â€“4, SDA=GPIO21, SCL=GPIO22)
- USB data cable (not charge-only)

Full BOM: `repo/hardware/BOM.md`

## Network / server setup

- **Mango GL.iNet router** â€” local classroom network
- WiFi SSID: `CECS`, Password: `CECS-Classroom`
- Laptop connects via Ethernet to Mango â†’ IP `192.168.8.10`
- ESP32 connects to `CECS` WiFi â†’ reaches MQTT broker at `192.168.8.10:1883`
- Server runs at `http://192.168.8.10:5000`
- Instructor dashboard: `http://192.168.8.10:5000/cecs460/instructor` (PIN: 4600)
- Student login: `http://192.168.8.10:5000/cecs460/login`

**Note:** `192.168.8.10` is DHCP â€” may change. Run `ipconfig` to verify.

## Starting the server

```bash
START_SERVER.bat        # Windows â€” double-click or run from terminal
# OR
cd repo/classroom-server && python run.py
```

## Expo demo mode

`repo/DEMO_MODE.bat` is the one-click launcher for the live expo. It:

1. Detects the laptop's LAN IP via PowerShell (Get-NetIPAddress, prefers DHCP/Manual non-APIPA), prompts for confirmation
2. Stops any prior `python.exe` so port 5000 is free
3. Starts the classroom server in a separate cmd window
4. Polls `http://localhost:5000/` until it responds (up to 25 s)
5. POSTs to `/cecs460/session/clear` with PIN 4600 to wipe leftover state
6. Opens `presentation.html`, the instructor dashboard, and the projector view

`presentation.html` is a single-file slide deck (no build step). Keys: â† / â†’ / Space navigate, **S** toggles presenter notes, **D** opens a demo-link launcher (configurable IP, persisted in localStorage), **F** fullscreen, **Esc** closes overlays. Touch swipe also works for tablets.

## Key commands

```bash
# Validate grading rubric against sample answers (run before any grading.json changes)
python3 repo/tests/test_grading.py

# Start the classroom server
START_SERVER.bat
```

## Step 4 firmware â€” MQTT pass design

`repo/hardware/starter_code/step4_accelerator/step4_accelerator.ino`

**Student modification task:** change `#define USE_DMA 0` to `1` at the top of the file.

- `USE_DMA=0`: software `analogRead()` loop â€” same lag as Step 2, ~40â€“80 Hz
- `USE_DMA=1`: ESP32 DMA controller fills ADC buffer at 10 kHz â€” LCD smooth, ~400â€“500 Hz

**Pass trigger:** when DMA rate holds above 200 Hz for 5 seconds, firmware connects to WiFi/MQTT and publishes `{answers: {q4_lab_pass: "PASS"}, chapter: "ch11Lab"}` to `c460_ch11_codesign/{slot}/answer`. Server scores it 10/10 (100%), dashboard shows pass.

**ch11Lab:** `classroom-server/classes/cecs460/lessons/ch11Lab/grading.json` â€” old-schema grading file with just `q4_lab_pass`, used only by firmware MQTT submissions (not the browser lesson).

**Required libraries (Arduino IDE Library Manager):**
- LiquidCrystal I2C (Frank de Brabander)
- PubSubClient (Nick O'Leary) â€” v2.8.x
- ArduinoJson (Benoit Blanchon) â€” v6.x

**Network config `#define`s at top of sketch** (change if IP/SSID differs):
```cpp
#define WIFI_SSID  "CECS"
#define WIFI_PASS  "CECS-Classroom"
#define MQTT_HOST  "192.168.8.10"
#define MQTT_PORT  1883
```

## scoring_engine.py fix

`core/scoring_engine.py` now handles both grading schemas:
- Old: `q["id"]`, `q["points"]`, `q["keywords"]`
- New (our lesson): `q["question_id"]`, `q["max_points"]`, `q["scoring"]["required_concepts"]`

The fix: `q.get("id") or q.get("question_id", "")` and `q.get("points") or q.get("max_points", 0)`. Without this, MQTT answer submissions would crash with KeyError.

## Syncing ch11Final

`ch11Final/` is the folder the server loads at runtime. Keep it in sync with `lesson_package/`:

```bash
cp repo/lesson_package/lesson.json   repo/classroom-server/classes/cecs460/lessons/ch11Final/
cp repo/lesson_package/grading.json  repo/classroom-server/classes/cecs460/lessons/ch11Final/
```

## What still needs to be done

### Must complete before submission

| Item | Notes |
|------|-------|
| **Testing evidence** | Flash each sketch, screenshot Serial Monitor output, screenshot instructor dashboard showing a pass. Save to `testing_evidence/`. Requires physical hardware. |
| **Recorded demo video (5â€“10 min)** | Walk through from student + instructor perspective, show server pass. Requires server + ESP32. |
| **Final report PDF export** | `docs/final_report.md` is complete; needs export to PDF for submission per spec. |

### Done

| Item | Status |
|------|--------|
| ch11Final synced with lesson_package | âœ… |
| MQTT pass in step4 firmware (USE_DMA task) | âœ… |
| ch11Lab grading.json for firmware pass | âœ… |
| scoring_engine.py crash fix | âœ… |
| step2_wiring.svg | âœ… `lesson_package/assets/step2_wiring.svg` |
| Instructor notes steps 1â€“5 | âœ… `lesson_package/instructor_notes/` |
| Contribution statement | âœ… `docs/contribution_statement.md` (Nathan Sarkozy + Christian Vanegas) |
| Expo slides outline | âœ… `docs/expo_slides_outline.md` |
| Expo presentation deck | âœ… `repo/presentation.html` (standalone, key-driven) |
| Demo mode launcher | âœ… `repo/DEMO_MODE.bat` |

## Professor's reference firmware

`repo/hardware/solution_code/CECS460_Lab11_AES/CECS460_Lab11_AES.ino` â€” professor's AES benchmark firmware. Do not distribute to students â€” instructor-only reference.
