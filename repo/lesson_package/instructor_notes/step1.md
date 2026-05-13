# Instructor notes -- Step 1: A blink that almost works

## Step intent

The opening step has one job: **anchor students in the surprising observation that ESP32 + FreeRTOS keeps a clean baseline blink at exactly 1.0000 Hz, then make them explain why this perfect timing is fragile.** Everything else in the lesson depends on them having invested in this first question -- it sets up the contrast for Step 2 (when contention destroys the perfection) and Step 4 (when the DMA fix restores it on different terms).

Do not front-load vocabulary. Words like "partitioning," "peripheral," "co-design," and "offload" should not appear in your introduction to Step 1. They appear naturally in Step 3 and Step 4 as labels for things students have already felt.

## Expected student measurements

The `step1_baseline.ino` firmware prints the measured period and frequency to Serial Monitor (115200 baud) after every full blink cycle, using `micros()` resolution so the period is shown to three decimal places.

Students will see lines like `Period: 1000.000 ms | Frequency: 1.0000 Hz` -- typically **the period reads 1000.000 ms exactly, every cycle**. This is the modern reality: the ESP32's hardware timer drives the FreeRTOS tick at 1 kHz, the tick drives `delay()`, and with the CPU otherwise idle every cycle resumes on the exact next tick. The result is a perfect 1,000,000 us period as measured by `micros()`.

This is **not** the older AVR-Arduino behavior where students would see ~0.998 Hz with visible drift. The narrative was rewritten to match what students will actually observe on modern ESP32-class hardware.

If a student reports a frequency wildly outside `1.0000 +/- 0.001` Hz, something is wrong -- most likely Serial Monitor is set to a different baud rate, or the wrong sketch is flashed, or another task is unexpectedly running on the CPU.

## Common student mistakes

| Mistake | What to do |
|---|---|
| LED doesn't light up | Check polarity (anode to GPIO side, cathode to GND). Check that the sketch actually compiled and uploaded -- look for "Hard resetting via RTS pin..." in the upload log. |
| No Serial output at all | Wrong baud rate in Serial Monitor. Set to 115200. |
| Garbled Serial output | Either wrong baud or charge-only USB cable. A charge-only cable will sometimes appear as a COM port but pass nothing usable. |
| No COM port appears | Charge-only USB cable; swap it for a data cable. |
| Student sees integer ms only (no decimals) | They flashed an OLD copy of the sketch that uses `millis()` instead of `micros()`. Re-pull the latest `step1_baseline.ino` and reflash. |
| Student is confused that their reading is exactly 1.0000 Hz | This is the correct, expected behavior on ESP32 + FreeRTOS. Direct them to the Q1 prompt -- the question is **why this perfect baseline is fragile**, not why it isn't perfect. |
| Student's answer to Q1 blames the hardware | Gently redirect: "The chip is working correctly. The question is what kind of *workload* would break the perfect timing -- and why the CPU is the bottleneck." |

## Grading guidance for Q1

Full credit (10 pts) requires recognition of both:
1. **CPU is a shared, single-task-at-a-time resource** (keywords: shared, single core, one task, compete, sequential)
2. **What kind of workload would break the perfect alignment** (keywords: load, another task, heavy computation, contention, busy, starve, concurrent)

Bonus credit for any awareness of the FreeRTOS scheduler / tick mechanism (keywords: scheduler, FreeRTOS, RTOS, tick, yields, wait its turn, preempt).

Most students will land in the 6-9 point range. That's fine -- this is the opening step. A student who writes "the CPU only runs one task at a time, so a heavy background task would push delay() off the perfect tick" earns full credit cleanly and is well-positioned for Step 2.

Do not penalize informal or casual language. The rubric rewards accurate *understanding*, not polished *writing*.

## Time budget

Budget 12 minutes for this step. Students who finish in under 8 minutes probably rushed the measurement -- check that they actually watched 10 cycles. Students who take more than 15 minutes are usually stuck on wiring or USB driver setup; walk around and spot-check.

## Why this opening works (revised narrative)

- **Fast hands-on:** students touch hardware within 3 minutes.
- **A surprise they see themselves:** the Serial Monitor reading IS exactly 1.0000 Hz, which contradicts the AVR-era "software is always slightly imprecise" assumption most have absorbed elsewhere.
- **A pivot, not a reveal:** instead of "explain why your reading isn't perfect," the question is "explain why this perfect baseline is fragile." That pivot sets up Step 2 (contention destroys it) more directly than the old framing did.

By the end of Step 1, students have committed to a mental model that says "software timing is precise UNTIL contention happens." That commitment is what powers the visceral reaction in Step 2 when they see the LCD lag under load.

## What not to do

- Do not introduce the word "peripheral" in this step.
- Do not explain the DMA or LEDC peripherals yet -- those land in Step 4.
- Do not say "this is about hardware/software co-design." Students will figure that out on their own in Step 4.
- Do not give students the answer before they've written their own. The reveal block is *after* their short-answer submission, not before.
- Do not let a student who reports "exactly 1.0000 Hz" think their setup is broken. Affirm it -- that's the correct observation.

## Required materials (this step only)

- 1 ESP32 DevKit per team
- 1 breadboard per team
- 1 standard LED per team (5 mm, any color)
- 1x 330 Ohm resistor per team
- 2 jumper wires per team
- 1 USB **data** cable per team (charge-only cables will not enumerate a COM port)

No oscilloscope is needed. All measurement is via Arduino IDE Serial Monitor.

## Prep checklist for the instructor

- [ ] Confirm `step1_baseline.ino` compiles cleanly with the current arduino-esp32 core before class
- [ ] Confirm at least one spare data-capable USB cable per row of teams (this is the most common day-of failure)
- [ ] Have a canonical Serial Monitor screenshot from `testing_evidence/step1_serial_monitor.png` available to show students if their output looks unexpected
- [ ] Pre-flash one demo ESP32 and have it printing live in Serial Monitor when students walk in -- sets the tone immediately
