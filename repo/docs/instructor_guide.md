# Instructor Guide — Chapter 11: Hardware/Software Co-Design

**Module:** CECS 460 Chapter 11 — Hardware/Software Co-Design and Design Flow
**Prepared for:** Spring 2026, future semesters
**Estimated class time:** ~90 minutes for all 5 steps

---

## What this module does

Students experience hardware/software partitioning firsthand rather than reading about it. The arc is:

1. **Step 1** — blink an LED; measure that software timing isn't perfect (Serial Monitor)
2. **Step 2** — add a potentiometer + LCD; run a CPU load; watch the display lag
3. **Step 3** — quantify the failure via Serial Monitor sample rate
4. **Step 4** — reflash with DMA firmware; same load, no lag; measure the improvement
5. **Step 5** — apply the decision framework to new scenarios; write a partitioning rule

The failure and the fix are both visible and measurable with no oscilloscope — only Serial Monitor is needed.

---

## Why this is better than the original chapter material

The professor's original Ch11 lab used an AES-128 software vs. hardware benchmark: students flash firmware, wait for MQTT telemetry, and compare microsecond timing numbers. That's accurate but abstract — students never feel the problem, they just read numbers.

This module makes the consequence physical: the LCD lags behind the knob. Students feel the failure before they understand it. The fix (DMA) is equally physical — same circuit, different firmware, the lag vanishes. The decision matrix in Step 5 then asks them to generalize from their own measured data.

---

## Hardware required (per team)

See `hardware/BOM.md` for sourcing and cost.

| Item | Qty | Notes |
|---|---|---|
| ESP32 DevKit (38-pin) | 1 | USB-C preferred |
| Breadboard (full size) | 1 | |
| Jumper wires | 1 kit | M-M, M-F |
| Standard LED (5 mm) | 1 | Any color |
| 330 Ω resistor | 1 | LED current limit |
| Potentiometer (10 kΩ) | 1 | |
| 16×2 LCD with I2C backpack | 1 | I2C address 0x27 |
| USB data cable | 1 | **Not charge-only** |

No oscilloscope required. No external power supply required.

---

## Software required

- Arduino IDE 2.x
- arduino-esp32 board package v3.x (Espressif, via Board Manager)
- LiquidCrystal_I2C library (Library Manager)

Full build/flash instructions: `hardware/starter_code/README.md`

---

## Deploying the lesson into the classroom system

1. Copy `lesson_package/` contents into the classroom server's chapter directory:
   ```
   repo/classroom-server/classes/cecs460/lessons/ch11Final/
   ```
   Overwrite `lesson.json` and `grading.json` with the versions from `lesson_package/`.

2. Confirm `classroom-server/classes/cecs460/class_config.json` has:
   ```json
   "active_lesson": "ch11Final"
   ```

3. Start the server:
   ```
   START_SERVER.bat
   ```
   or
   ```
   cd repo/classroom-server && python run.py
   ```

4. Open the instructor dashboard: `http://192.168.8.228:5000/cecs460/instructor` (PIN: 4600)

5. Test: log in as a student at `http://192.168.8.228:5000/cecs460/login`, navigate to Step 1, confirm it loads correctly.

> **Note:** `192.168.8.228` is the laptop IP on the Mango GL.iNet router (SSID: `DEEZ`). If the IP changes, run `ipconfig` to find the new one and update it with `CHANGE_IP.bat`.

---

## Running the class session

### Before students arrive

- [ ] Start the classroom server (`START_SERVER.bat`)
- [ ] Confirm instructor dashboard loads
- [ ] Pre-wire one demo board with Step 2 circuit and have Serial Monitor running — shows students the lag immediately as they walk in
- [ ] Confirm `step1_baseline.ino`, `step2_overload.ino`, `step4_accelerator.ino` all compile cleanly on your machine

### Step 1 (~12 min)

Students wire LED to GPIO 18, flash `step1_baseline.ino`, open Serial Monitor, read the frequency printed each cycle. Expected range: 0.996–1.004 Hz. Answer Q1.

**Common issues:**
- LED doesn't light → check polarity (anode to GPIO side)
- No Serial output → check baud rate is 115200
- No COM port → charge-only USB cable; swap it

### Step 2 (~15 min)

Students add potentiometer (GPIO 34) and LCD (I2C, GPIO 21/22), flash `step2_overload.ino`. Turn the knob — the LCD lags. Serial Monitor shows sample rate (~40–80 Hz typically). Answer Q2.

**Common issues:**
- LCD blank → check I2C address (default 0x27; some modules use 0x3F)
- LCD garbled text → bad SDA/SCL wiring or wrong I2C address
- No lag visible → increase `LOAD_STRENGTH` in the sketch (default 5000; try 20000)

### Step 3 (~15 min)

No reflash. Students read Serial Monitor, record sample rate, compare against the 50 Hz hypothetical requirement. Answer Q3.

### Step 4 (~20 min)

Students flash `step4_accelerator.ino` — same wiring. LCD becomes smooth. Serial Monitor shows `[DMA]` sample rate (~400–500 Hz typically). Answer Q4.

**Common issues:**
- `driver/i2s.h` not found → wrong arduino-esp32 version; must be 3.x
- Sample rate not much higher → confirm step4 is flashed (not step2); check Serial output prefix `[DMA]` vs `[SW]`

### Step 5 (~20 min)

No hardware. Students fill in the decision matrix and write Q5 in the lesson system.

---

## Grading

Answers are scored by keyword-weighted matching in `lesson_package/grading.json`. The server grades automatically on submission and displays results in the instructor dashboard.

| Question | Max pts | Key concept |
|---|---|---|
| Q1 — Why not exact? | 10 | Software timing + CPU interrupts |
| Q2 — Why lag? | 10 | CPU as shared resource |
| Q3 — What does the rate mean? | 10 | Sample rate as a deadline metric |
| Q4 — What did DMA do? | 10 | Autonomous hardware, parallel execution |
| Q5 — Your rule | 10 | Measure-first + reference own data |

Full grading rubric with exemplars: `lesson_package/grading.json`

To validate the rubric against sample answers before class:
```bash
python3 tests/test_grading.py
```

---

## Common student mistakes (all steps)

| Mistake | Step | Fix |
|---|---|---|
| Charge-only USB cable | 1–4 | Replace — no COM port will appear |
| ESP32 boot mode | 1–4 | Hold BOOT button during upload on some boards |
| LCD address wrong | 2–4 | Change `0x27` to `0x3F` in sketch line 24 |
| Measures Step 2 sample rate as Step 4 | 4 | Have them check Serial output for `[DMA]` prefix |
| Q5 answer: "always use hardware" | 5 | Redirect: when does hardware actually help? What did your numbers show? |

---

## Recommendations for next semester

1. **Add a step 3 firmware variant** that lets students adjust `LOAD_STRENGTH` via Serial command so they can find the exact threshold where the sample rate drops below 50 Hz.
2. **Add a WS2812 LED strip** as a more dramatic visual — a 16-pixel bar graph lagging is more visually striking than an LCD number.
3. **Add MQTT pass reporting** to the starter firmware so the server dashboard shows green when students complete Step 4 successfully.
4. **Record canonical Serial Monitor captures** for each step so students have a reference when their output looks unexpected.
