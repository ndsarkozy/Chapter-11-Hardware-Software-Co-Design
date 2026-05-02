# Expo Presentation Outline — CECS 460 Chapter 11 Module
## Hardware/Software Co-Design and Design Flow
**Nathan Sarkozy — Spring 2026 Final Expo**

---

### Slide 1 — Title
- **Chapter 11: Hardware/Software Co-Design**
- "When does software stop being enough?"
- One-sentence hook: "You're going to watch a microcontroller fail — and then fix it in 90 seconds by changing one line of code."

---

### Slide 2 — The Problem We Solved
- Original Chapter 11 lab: AES encryption benchmark (measure timing → submit number)
- Weakness: passive, no visible failure, no intuition for *why* hardware matters
- Our approach: make the failure visible and physical — a lagging potentiometer display

---

### Slide 3 — The Hardware (30 seconds setup)
- ESP32 + 16×2 LCD + potentiometer
- Show actual hardware on the table
- "This is everything. No oscilloscope, no special equipment."

---

### Slide 4 — Live Demo: Step 2 (The Failure)
- Flash `step2_overload.ino` — show LCD lagging behind knob
- Point at Serial Monitor: "About 42 Hz. Requirement is 50 Hz. System fails."
- "The CPU is shared. The load task is winning. The ADC read is losing."

---

### Slide 5 — Live Demo: Step 4 (The Fix)
- Show `step4_accelerator.ino` with `USE_DMA 0`
- "This is what students start with — same lag as Step 2."
- Change `USE_DMA` to `1`, flash (30 seconds), show LCD smooth
- Serial Monitor: "428 Hz. 10× improvement. Same load, same hardware."
- Point at LCD when it shows `DMA PASS SENT!`

---

### Slide 6 — The Server Pass
- Show instructor dashboard on laptop — slot shows as passed
- "No manual entry. The firmware measured its own performance and reported it."
- "Students know they passed because the server says so, not because they think they did it right."

---

### Slide 7 — Design Decisions
Three key tradeoffs we made:
1. **LCD over oscilloscope** — visible to everyone in the room, no extra equipment
2. **USE_DMA flag** — one-line modification tests real understanding, not copy-paste
3. **Serial Monitor over black-box result** — students see the Hz number before and after

---

### Slide 8 — What Students Learn
| Concept | How the module teaches it |
|---|---|
| CPU is a shared resource | Watch it lag in Step 2 |
| Measurement before optimization | Record Hz in Step 3 before fixing |
| HW/SW tradeoff is requirement-driven | Compare rates, write their own rule in Step 5 |
| Server integration | Firmware publishes pass automatically |

---

### Slide 9 — Grading & Assessment
- 5 short-answer questions, keyword-weighted rubric
- Automated scoring via classroom server
- All 35 test cases pass (`python3 repo/tests/test_grading.py`)
- Questions escalate: observe → diagnose → compare → synthesize → generalize

---

### Slide 10 — What's Left for Next Semester
- Hardware tested? Yes *(show testing evidence screenshots)*
- Server pass confirmed end-to-end? Yes *(show dashboard screenshot)*
- Suggestions for future improvement: add a second core demo (FreeRTOS task pinned to Core 0 vs Core 1) to show the dual-core alternative to DMA

---

### Backup slide — System Architecture
```
ESP32 Firmware
  ├─ loop() — runs CPU load + ADC read + LCD update
  ├─ maintainNetwork() — WiFi + MQTT reconnect
  └─ publishPass() — fires once when DMA rate > 200 Hz × 5 s
          ↓ MQTT
ClassroomFusion Server
  ├─ mqtt_bridge.py — receives answer, scores via ch11Lab/grading.json
  ├─ sse.py — pushes pass event to instructor dashboard
  └─ attendance.py — records checkin with bonus=True
```
