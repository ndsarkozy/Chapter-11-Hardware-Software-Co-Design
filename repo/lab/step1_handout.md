# CECS 460 — Chapter 11 Lab
## Step 1: A blink that almost works

**Time:** ~12 minutes
**You will need:** ESP32 DevKit, breadboard, 1 standard LED, 1x 330 Ω resistor, 2 jumper wires, oscilloscope

---

### What you're doing

Blinking an LED is the first thing anyone does with a microcontroller. You've done it many times. Today you're going to do it again — but this time, you're going to *measure* it, and you're going to find it isn't quite what you expected.

### Wire it up

1. Place your ESP32 on the breadboard.
2. From **GPIO 18**, run a wire to one end of a **330 Ω resistor**.
3. From the other end of the resistor, run a wire to the **anode** (longer leg) of the LED.
4. From the **cathode** (shorter leg) of the LED, run a wire to the **GND** rail.
5. Connect your **scope probe tip** to **GPIO 18**. Clip the probe ground to the **GND** rail.

### Flash it

Open `hardware/starter_code/step1_baseline/step1_baseline.ino` and upload it to your ESP32. The LED will start blinking at roughly once per second.

### Measure it

Configure your scope:

- **Timebase:** 200 ms/div
- **Channel 1 coupling:** DC, 2 V/div
- **Trigger:** CH1, rising edge, ~1.5 V level

Use your scope's auto-measure feature to read the **frequency**. Record it to four decimal places.

| My measurement | |
|---|---|
| Frequency (Hz) | __________ |
| Is it exactly 1.0000 Hz? | [ ] Yes  [ ] No |

*(Spoiler: nobody in this class will measure exactly 1.0000 Hz.)*

### Think about it

> **Q1 (short answer, graded):** Your scope reading isn't exactly 1.0000 Hz. In 2–3 sentences, explain why. What is the ESP32 actually doing, and why can't the software produce a perfect 1 Hz signal?

Write your answer in the lesson system's Step 1 short-answer box. You'll get immediate scoring feedback.

### What's next

A ~0.3% frequency error is probably invisible to you right now. In Step 2, we're going to turn up the difficulty until the imperfection becomes impossible to miss.
