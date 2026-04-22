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
