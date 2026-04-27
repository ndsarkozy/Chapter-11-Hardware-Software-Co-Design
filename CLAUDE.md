# CECS 460 — Chapter 11 Module

## What this is

Final project for CECS 460 (System on Chip) at CSULB, Spring 2026, by Nathan Sarkozy and partner. An interactive classroom module for Chapter 11: Hardware/Software Co-Design. Students learn hardware/software partitioning by watching software fail under load on an ESP32, then fixing it with a dedicated hardware peripheral.

Plugs into the ClassroomFusion server system — the full server lives at `repo/classroom-server/`.

## Repo layout

```
repo/
  classroom-server/       # Full ClassroomFusion server (run this to host the lesson)
    run.py                # Entry point — starts MQTT broker + Flask server
    requirements.txt
    core/                 # UI engine: server, dashboard, MQTT, scoring, SSE
    classes/cecs460/      # CECS 460 specific routes + ch11 lesson/grading JSON
  hardware/
    starter_code/         # Arduino sketches students flash, by step
    solution_code/        # Reference implementations (instructor only)
      CECS460_Lab11_AES/  # Professor's AES benchmark firmware (reference)
    BOM.md
  docs/
    professor_reference/  # Professor's original lesson.json, grading.json, LAB11_TEXTBOOK_SECTION.md
    instructor_guide.md
    final_report.md
    contribution_statement.md
  lesson_package/         # Our lesson content (what the classroom system loads)
    lesson.json
    grading.json
    assets/
    instructor_notes/
  lab/                    # Student-facing handouts (one per step)
  testing_evidence/       # Screenshots, grading test output
  tests/
    test_grading.py       # Automated checks for grading.json rubric
  START_SERVER.bat        # Double-click to start the classroom server
  STOP_SERVER.bat
  CHANGE_IP.bat
```

## 5-step lesson (~2 hours)

No oscilloscope — all failures and fixes must be visible to the naked eye or Serial Monitor.

| Step | Title | Status |
|------|-------|--------|
| 1 | A blink that almost works — measure software-timed 1 Hz signal, notice drift | Complete |
| 2 | Software under pressure — potentiometer + WS2812 bar graph lags under CPU load | Not started |
| 3 | Why did it fail? — diagnose via Serial Monitor timing prints | Not started |
| 4 | The accelerator — swap ADC polling to DMA, bar graph stays smooth under same load | Not started |
| 5 | The partition decision — fill in decision matrix | Not started |

Instructor guide: in progress. Final report: not started.

## Lesson concept (Steps 2–4)

- **Hardware:** Potentiometer wired to ESP32 ADC + WS2812 16-pixel LED strip as bar graph
- **Step 2 failure:** CPU polls ADC in software loop while background load task runs → bar graph lags/stutters visibly when knob is turned
- **Step 3 diagnose:** Print ADC sample timestamps to Serial Monitor — students see sample rate drop under load
- **Step 4 fix:** Switch to DMA-based ADC — DMA controller fills buffer autonomously, CPU just reads results → bar graph stays responsive under same load
- **Hardware offload used:** ESP32 DMA controller (built-in, no external hardware needed beyond potentiometer)
- **Why DMA:** Teaches the core co-design concept — dedicated hardware block handles data movement so CPU is free

## Hardware

- ESP32 DevKit
- Standard LED + 330 Ω resistor (step 1)
- 16-pixel WS2812 addressable LED strip + 470 Ω resistor + 1000 µF capacitor (steps 2–5)
- Potentiometer (steps 2–5, wired to ADC pin)
- Pushbutton + 10 kΩ pull-down resistor
- NO oscilloscope in this setup

Full BOM: `repo/hardware/BOM.md`

## Network / server setup

- **Mango GL.iNet router** used as local classroom network
- WiFi SSID: `DEEZ`, Password: `password`
- Laptop connects via **Ethernet** to Mango → gets IP `192.168.8.228`
- ESP32 connects to `DEEZ` WiFi → reaches MQTT broker at `192.168.8.228:1883`
- Server (Flask + embedded MQTT) runs on laptop at `192.168.8.228:5000`
- Instructor dashboard: `http://192.168.8.228:5000/cecs460/instructor` (PIN: 4600)
- Student login: `http://192.168.8.228:5000/cecs460/login`

**Note:** `192.168.8.228` is DHCP — may change. Run `ipconfig` to verify. Override on ESP32 with serial command: `set mqtt <new_ip>`

## Starting the server

```bash
cd repo
START_SERVER.bat        # Windows — double-click or run from terminal
# OR
cd repo/classroom-server
python run.py           # Cross-platform
```

Server auto-starts embedded MQTT broker (amqtt) if Mosquitto is not installed.

## Professor's reference files

- `repo/docs/professor_reference/lesson.json` — professor's ch11 lesson (AES benchmark concept)
- `repo/docs/professor_reference/grading.json` — professor's grading rubric
- `repo/docs/professor_reference/LAB11_TEXTBOOK_SECTION.md` — lab handout
- `repo/hardware/solution_code/CECS460_Lab11_AES/CECS460_Lab11_AES.ino` — professor's ESP32 firmware

The professor's lesson uses AES SW vs HW benchmark as the co-design demo. Our lesson uses potentiometer + WS2812 + DMA — same concepts, more hands-on and visible.

## Key commands

```bash
# Run grading rubric tests before pushing changes to grading.json
python3 repo/tests/test_grading.py
```
