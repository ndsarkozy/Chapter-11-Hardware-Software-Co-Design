# CECS 460 — Chapter 11 Lab
## Step 2: Software Under Pressure

**Time:** ~15 minutes
**You will need:** ESP32 DevKit, breadboard, potentiometer (10 kΩ), 16×2 LCD with I2C backpack, jumper wires, USB data cable

---

### What you're doing

You're going to add more hardware and deliberately break the system. The ESP32 will read a potentiometer and display the value on an LCD — while simultaneously running a CPU-heavy background task. Watch what happens.

### Wire it up

Keep your Step 1 LED in place. Add the following:

**Potentiometer:**
| Pot pin | ESP32 pin |
|---|---|
| Left outer pin | GND |
| Middle pin (wiper) | GPIO 34 |
| Right outer pin | 3.3 V |

**LCD 16×2 (I2C backpack, address 0x27):**
| LCD pin | ESP32 pin |
|---|---|
| VCC | 5 V (VIN) |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |

### Flash it

Open `hardware/starter_code/step2_overload/step2_overload.ino` and upload it to your ESP32.

The LCD will show "CECS 460 Step 2" briefly, then start displaying the knob percentage.

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
