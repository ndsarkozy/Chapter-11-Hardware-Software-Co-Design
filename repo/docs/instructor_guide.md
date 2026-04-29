# Instructor guide — Chapter 11: Hardware/Software Co-Design

*This guide is 1–2 pages targeted at an instructor deploying the module next semester. It will be fleshed out as the module is completed.*

## What changed

*(To be written once all 5 steps are built.)*

## Why this version is better than the original chapter content

*(To be written.)*

## Required materials

See [`../hardware/BOM.md`](../hardware/BOM.md).

## Setup steps

1. Clone this repo onto a machine running the Interactive Classroom System
2. Copy `lesson_package/` into the system's chapter content directory:
   ```bash
   cp -r lesson_package /path/to/classroom_system/chapters/ch11/
   ```
3. Restart the classroom system
4. Verify Chapter 11 appears in the chapter list and Step 1 loads without errors
5. Pre-wire one demo board and have it running a scope capture when students arrive — it sets the tone

## Expected trouble spots

*(To be written based on testing.)*

- USB cable issues (charge-only cables vs. data cables)
- ESP32 boot mode problems (hold BOOT button during upload on some variants)
- WS2812 level-shifting issues on 3.3 V logic (step 2+)
- Scope trigger misconfiguration (step 1)

## Grading workflow

*(To be written.)*

## Lab: Three-LED Timing Demo (04_visual_demo.ino)

### Demo script (3-minute lecture version)

1. Boot at 5 Hz, LOAD=NONE. Show Serial output on projector. All three LEDs in sync — ask students to confirm they look the same.
2. Type `l` twice → HEAVY load. Point to LED 1 visibly beginning to stutter or slow. Ask: "What changed?"
3. Type `l` once more → BRUTAL. LED 1 is now clearly at a different cadence. Students can count the blinks.
4. Ask: "What is LED 3 doing that LED 2 isn't?" (Expected answer: LED 3 involves zero CPU after setup — no ISR, no interrupt, just a clock divider in silicon. LED 2 still runs a brief ISR on every timer fire.)
5. Type `r` to reset. Hand keyboard to a student.

### Common student mistakes

| Problem | Symptom | Fix |
|---------|---------|-----|
| LED wired backwards | LED doesn't light | Flip the LED — cathode to GND, anode through resistor to GPIO |
| Missing resistor | LED very bright then dies | Always use 220Ω in series |
| Wrong baud rate | Garbled Serial output | Set Serial Monitor to 115200 baud |
| Arduino-ESP32 core 2.x | Compile error on timerBegin() | Core 3.x uses `timerBegin(freq_hz)` — upgrade to core 3.x in Board Manager |
| LEDC no output | LED3 stays off | Confirm PIN_LEDC = 21 and `ledcAttach()` called before `ledcWrite()` |
| USB cable charge-only | No COM port appears | Replace with data-capable USB cable |

### Discussion questions (post-demo)

1. "If you were designing a smart thermostat that blinks an LED at different rates for heating/cooling/idle — which method would you use and why?" *(Expected: ISR or LEDC, because the rate must change at runtime based on sensor input. Pure LEDC can't react to inputs without CPU reconfiguration.)*

2. "LEDC is baked into the ESP32 silicon. Who paid for that decision, and who benefits?" *(Expected: Espressif paid the die area cost at tape-out. Every ESP32 user benefits from that partitioning decision for free. This is the tape-out economics argument from Section 11.2.3.)*

3. "What would break if you used pure LEDC and then needed to respond to a button press that changes blink rate?" *(Expected: LEDC has no inputs — it just runs a clock divider. The CPU must reconfigure the peripheral on every rate change. For purely static output LEDC wins; for reactive output ISR is more flexible.)*

### Grading notes

- q_predict: Watch for students who say "LEDC is best because it's hardware" without explaining the clock divider mechanism. That is a disqualifier — award partial credit only.
- q_measure: The key is a VISUAL description. Students who only quote Serial numbers did not observe the physical demo. Deduct heavily for this.
- Expected correct ranking: LEDC > ISR > SW (most to least accurate under load).
