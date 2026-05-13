# CECS 460 — Chapter 11 Lab
## Step 1: A blink that almost works

**Time:** ~12 minutes
**You will need:** ESP32 DevKit, breadboard, 1 standard LED, 1x 330 Ω resistor, 2 jumper wires, USB data cable

---

### What you're doing

Blinking an LED is the first thing anyone does with a microcontroller. You've done it many times. Today you're going to do it again — but this time, you're going to *measure* it carefully, and you're going to learn something surprising about how the ESP32 keeps time.

### Wire it up

1. Place your ESP32 on the breadboard.
2. From **GPIO 18**, run a wire to one end of a **330 Ω resistor**.
3. From the other end of the resistor, run a wire to the **anode** (longer leg) of the LED.
4. From the **cathode** (shorter leg) of the LED, run a wire to the **GND** rail.

### Flash it

Open `hardware/starter_code/step1_baseline/step1_baseline.ino` and upload it to your ESP32. The LED will start blinking at roughly once per second.

### Measure it

Open **Serial Monitor** in Arduino IDE (Tools → Serial Monitor, baud **115200**).

After every full blink cycle, the firmware prints the measured period and frequency:

```
Period: 1000.000 ms  |  Frequency: 1.0000 Hz
Period: 1000.000 ms  |  Frequency: 1.0000 Hz
```

Watch it for about 10 cycles, then record a representative value.

| My measurement | |
|---|---|
| Frequency (Hz) | __________ |
| Is it exactly 1.0000 Hz? | [ ] Yes  [ ] No |

*(Spoiler: most ESP32s on this clean baseline will measure exactly 1.0000 Hz. That's not a measurement error — the FreeRTOS scheduler aligns `delay(500) + delay(500)` to the hardware tick when nothing else is competing for the CPU.)*

### Think about it

> **Q1 (short answer, graded):** Your Serial Monitor reads exactly 1.0000 Hz cycle after cycle. The ESP32's FreeRTOS scheduler keeps perfect tick alignment when the CPU has nothing else to do. In 2–3 sentences, explain why this perfect timing is fragile: what kind of workload would break it, and which CPU resource is the bottleneck?

Write your answer in the lesson system's Step 1 short-answer box. You'll get immediate scoring feedback.

### What's next

The baseline is perfect — until it isn't. In Step 2 you'll add a real CPU workload to the same hardware, and watch the same code lose its perfect timing. That's where the chapter's real point about hardware/software co-design begins.
