# CECS 460 — Chapter 11 Lab
## Step 2: Software Under Pressure

**Time:** ~15 minutes
**You will need:** ESP32 DevKit, breadboard, two 10 kΩ potentiometers (one for the signal, one for LCD contrast), 16×2 parallel LCD (TC1602A or any HD44780-compatible module), 220 Ω resistor (for backlight, if your module has no built-in resistor), jumper wires, USB data cable

---

### What you're doing

You're going to add more hardware and deliberately break the system. The ESP32 will read a potentiometer and display the value on an LCD — while simultaneously running a CPU-heavy background task. Watch what happens.

### Wire it up

The LED from Step 1 is no longer used (you can leave it in or remove it). Add the following:

**Signal potentiometer (the knob the firmware reads):**
| Pot pin | ESP32 pin |
|---|---|
| Left outer pin | GND |
| Middle pin (wiper) | GPIO 34 |
| Right outer pin | 3.3 V |

**LCD 16×2 parallel (TC1602A, 4-bit mode):**
| LCD pin | Connect to | Notes |
|---|---|---|
| 1  · VSS | GND | |
| 2  · VDD | 5 V (VIN) | |
| 3  · V0  | wiper of contrast pot | outer pins of contrast pot to 5 V and GND |
| 4  · RS  | GPIO 19 | |
| 5  · RW  | GND | (write-only mode) |
| 6  · E   | GPIO 23 | enable |
| 7–10 · D0–D3 | leave unconnected | (we use 4-bit mode) |
| 11 · D4 | GPIO 18 | |
| 12 · D5 | GPIO 5  | |
| 13 · D6 | GPIO 17 | |
| 14 · D7 | GPIO 16 | |
| 15 · A  | 5 V (through 220 Ω if no built-in resistor) | backlight + |
| 16 · K  | GND | backlight − |

> **Two pots in this lab.** The *signal* pot is the one the firmware reads on GPIO 34 — turn this one to change the displayed value. The *contrast* pot is wired to V0 only — turn it once at startup to make the characters readable, then leave it.

### Library — already installed

The standard `LiquidCrystal` library that drives the parallel LCD is **built into Arduino IDE** — no Library Manager step needed. The sketch's `#include <LiquidCrystal.h>` finds it automatically.

### Flash it

Open `hardware/starter_code/step2_overload/step2_overload.ino` and upload it to your ESP32.

The LCD will show "CECS 460 Step 2" briefly, then start displaying the knob percentage.

> **LCD backlight on but no characters visible?** Turn the contrast pot. The display is working — the contrast just hasn't been adjusted to a usable level yet.
> **Random characters or only top row of solid blocks?** Double-check the D4–D7 wiring order — easy to swap two of them.
> **Backlight not on at all?** Verify pin 15 (A) is connected to 5 V (with the 220 Ω if you added one).

### Break it

Turn the potentiometer slowly back and forth. Then turn it quickly. Observe how fast the LCD percentage updates.

The bottom row of the LCD should read **`SW Poll  LAGGING`** — that message is there because the firmware already knows what's happening.

### Measure the damage

Open **Serial Monitor** (Tools → Serial Monitor, baud **115200**).

You will see lines like:

```
[SW] Sample rate: 42.3 Hz  |  Knob: 67%
[SW] Sample rate: 41.8 Hz  |  Knob: 68%
```

This is how many times per second the CPU actually read the ADC. Watch it for 30 seconds and record a representative value.

| My measurement | |
|---|---|
| Software ADC sample rate (Hz) | __________ |
| Does the LCD lag visibly behind the knob? | [ ] Yes  [ ] No |

### Think about it

> **Q2 (short answer, graded):** The CPU load task and the ADC polling loop share the same processor. In 2–3 sentences, explain why this causes the LCD to lag. What is the CPU doing when it should be reading the ADC?

Write your answer in the lesson system's Step 2 short-answer box.

### What's next

You have the broken system. In Step 3, you'll open Serial Monitor and put a real number on how broken it is.
