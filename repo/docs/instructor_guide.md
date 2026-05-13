# Instructor Guide â€” Chapter 11: Hardware/Software Co-Design

**Module:** CECS 460 Chapter 11 â€” Hardware/Software Co-Design and Design Flow
**Prepared for:** Spring 2026, future semesters
**Estimated class time:** ~90 minutes for all 5 steps

---

## What this module does

Students experience hardware/software partitioning firsthand rather than reading about it. The arc is:

1. **Step 1** â€” blink an LED; measure that software timing isn't perfect (Serial Monitor)
2. **Step 2** â€” add a potentiometer + LCD; run a CPU load; watch the display lag
3. **Step 3** â€” quantify the failure via Serial Monitor sample rate
4. **Step 4** â€” reflash with DMA firmware; same load, no lag; measure the improvement
5. **Step 5** â€” apply the decision framework to new scenarios; write a partitioning rule

The failure and the fix are both visible and measurable with no oscilloscope â€” only Serial Monitor is needed.

---

## Why this is better than the original chapter material

The professor's original Ch11 lab used an AES-128 software vs. hardware benchmark: students flash firmware, wait for MQTT telemetry, and compare microsecond timing numbers. That's accurate but abstract â€” students never feel the problem, they just read numbers.

This module makes the consequence physical: the LCD lags behind the knob. Students feel the failure before they understand it. The fix (DMA) is equally physical â€” same circuit, different firmware, the lag vanishes. The decision matrix in Step 5 then asks them to generalize from their own measured data.

---

## Hardware required (per team)

See `hardware/BOM.md` for sourcing and cost.

| Item | Qty | Notes |
|---|---|---|
| ESP32 DevKit (38-pin) | 1 | USB-C preferred |
| Breadboard (full size) | 1 | |
| Jumper wires | 1 kit | M-M, M-F |
| Standard LED (5 mm) | 1 | Any color |
| 330 Î© resistor | 1 | LED current limit |
| Potentiometer (10 kÎ©) | 2 | One for signal on GPIO 34, one for LCD V0 contrast |
| 16Ã—2 parallel LCD (TC1602A or HD44780-compatible) | 1 | 16-pin module, driven in 4-bit mode |
| 220 Î© resistor | 1 | LCD backlight current limit (skip if module has built-in resistor) |
| USB data cable | 1 | **Not charge-only** |

No oscilloscope required. No external power supply required.

---

## Software required

- Arduino IDE 2.x
- arduino-esp32 board package v3.x (Espressif, via Board Manager)
- LiquidCrystal library (built into Arduino IDE -- no install needed)
- PubSubClient and ArduinoJson v6.x (Library Manager, Step 4 only)

Full build/flash instructions: `hardware/starter_code/README.md`

---

## Deploying the lesson into the classroom system

1. Copy `lesson_package/` contents into the classroom server's chapter directory:
   ```
   repo/classroom-server/classes/cecs460/lessons/ch11/
   ```
   Overwrite `lesson.json` and `grading.json` with the versions from `lesson_package/`.

2. Confirm `classroom-server/classes/cecs460/class_config.json` has:
   ```json
   "active_lesson": "ch11"
   ```

3. Start the server:
   ```
   START_SERVER.bat
   ```
   or
   ```
   cd repo/classroom-server && python run.py
   ```

4. Open the instructor dashboard: `http://192.168.8.10:5000/cecs460/instructor` (PIN: 4600)

5. Test: log in as a student at `http://192.168.8.10:5000/cecs460/login`, navigate to Step 1, confirm it loads correctly.

> **Note:** `192.168.8.10` is the laptop IP on the Mango GL.iNet router (SSID: `CECS`). If the IP changes, run `ipconfig` to find the new one and update it with `CHANGE_IP.bat`.

---

## Running the class session

### Before students arrive

- [ ] Start the classroom server (`START_SERVER.bat`)
- [ ] Confirm instructor dashboard loads
- [ ] Pre-wire one demo board with Step 2 circuit and have Serial Monitor running â€” shows students the lag immediately as they walk in
- [ ] Confirm `step1_baseline.ino`, `step2_overload.ino`, `step4_accelerator.ino` all compile cleanly on your machine

### Step 1 (~12 min)

Students wire LED to GPIO 18, flash `step1_baseline.ino`, open Serial Monitor, read the frequency printed each cycle. Expected range: 0.996â€“1.004 Hz. Answer Q1.

**Common issues:**
- LED doesn't light â†’ check polarity (anode to GPIO side)
- No Serial output â†’ check baud rate is 115200
- No COM port â†’ charge-only USB cable; swap it

### Step 2 (~15 min)

Students wire signal pot (GPIO 34), contrast pot (LCD V0), and 16x2 parallel LCD (RS=GPIO19, EN=GPIO23, D4=GPIO18, D5=GPIO5, D6=GPIO17, D7=GPIO16). Flash `step2_overload.ino`. Turn the knob -- the LCD lags. Serial Monitor shows sample rate (~40-80 Hz typically). Answer Q2.

**Common issues:**
- LCD backlight on, blank screen -> turn the contrast pot (V0)
- LCD backlight off -> verify pin 15 (A) -> 5V (through 220 ohm if no built-in resistor), pin 16 (K) -> GND
- Random characters / only top row of solid blocks -> D4-D7 wiring order swapped
- No lag visible -> increase `LOAD_STRENGTH` in the sketch (default 5000; try 20000)

### Step 3 (~15 min)

No reflash. Students read Serial Monitor, record sample rate, compare against the 50 Hz hypothetical requirement. Answer Q3.

### Step 4 (~20 min)

Students flash `step4_accelerator.ino` â€” same wiring. LCD becomes smooth. Serial Monitor shows `[DMA]` sample rate (~400â€“500 Hz typically). Answer Q4.

**Common issues:**
- `driver/i2s.h` not found â†’ wrong arduino-esp32 version; must be 3.x
- Sample rate not much higher â†’ confirm step4 is flashed (not step2); check Serial output prefix `[DMA]` vs `[SW]`

### Step 5 (~20 min)

No hardware. Students fill in the decision matrix and write Q5 in the lesson system.

---

## Grading

Answers are scored by keyword-weighted matching in `lesson_package/grading.json`. The server grades automatically on submission and displays results in the instructor dashboard.

| Question | Max pts | Key concept |
|---|---|---|
| Q1 -- Why is the perfect baseline fragile? | 10 | CPU as shared resource + what would break it |
| Q2 â€” Why lag? | 10 | CPU as shared resource |
| Q3 â€” What does the rate mean? | 10 | Sample rate as a deadline metric |
| Q4 â€” What did DMA do? | 10 | Autonomous hardware, parallel execution |
| Q5 â€” Your rule | 10 | Measure-first + reference own data |

Full grading rubric with exemplars: `lesson_package/grading.json`

To validate the rubric against sample answers before class:
```bash
python3 tests/test_grading.py
```

---

## Common student mistakes (all steps)

| Mistake | Step | Fix |
|---|---|---|
| Charge-only USB cable | 1â€“4 | Replace â€” no COM port will appear |
| ESP32 boot mode | 1â€“4 | Hold BOOT button during upload on some boards |
| LCD blank but backlit | 2-4 | Adjust contrast pot wired to V0 |
| LCD random chars / top row solid | 2-4 | D4-D7 wiring order swapped |
| Measures Step 2 sample rate as Step 4 | 4 | Have them check Serial output for `[DMA]` prefix |
| Q5 answer: "always use hardware" | 5 | Redirect: when does hardware actually help? What did your numbers show? |

---

## Recommendations for next semester

1. **Add a step 3 firmware variant** that lets students adjust `LOAD_STRENGTH` via Serial command so they can find the exact threshold where the sample rate drops below 50 Hz.
2. **Add a WS2812 LED strip** as a more dramatic visual â€” a 16-pixel bar graph lagging is more visually striking than an LCD number.
3. **Record canonical Serial Monitor captures** for each step so students have a reference when their output looks unexpected.
4. **Add a dual-core Step 4b** comparing FreeRTOS task pinning (Core 0 vs Core 1) against the DMA approach â€” gives students a second partitioning option to weigh.
