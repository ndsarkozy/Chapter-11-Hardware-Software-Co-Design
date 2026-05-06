# Instructor notes — Step 1: A blink that almost works

## Step intent

The opening step has one job: **get students to commit to a mental model about why software timing isn't perfect, without naming the concept yet.** Everything else in this lesson depends on them having invested in this first question.

Do not front-load vocabulary. Words like "partitioning," "peripheral," "co-design," and "offload" should not appear in your introduction to Step 1. They appear naturally in Step 3 and Step 4 as labels for things students have already felt.

## Expected student measurements

The `step1_baseline.ino` firmware prints the measured period and frequency to Serial Monitor (115200 baud) after every full blink cycle. Students will see lines like `Period: 1002 ms | Frequency: 0.9980 Hz`.

Frequencies will land in the range **0.996 to 1.004 Hz**. The dominant source of drift is the Arduino core's RTOS tick and the handful of microseconds `delay()` rounds against the tick period. The exact number varies per board — crystal tolerance, temperature, and WiFi/BT radio state all contribute. **This is a feature, not a bug.** Every student's reading is slightly different, which makes copying meaningless and drives genuine engagement with the question.

If a student reports a frequency wildly outside this range (< 0.9 or > 1.1), something is wrong — most likely Serial Monitor is set to a different baud rate, or the wrong sketch is flashed.

## Common student mistakes

| Mistake | What to do |
|---|---|
| LED doesn't light up | Check polarity (anode to GPIO side, cathode to GND). Check that the sketch actually compiled and uploaded — look for "Hard resetting via RTS pin..." in the upload log. |
| No Serial output at all | Wrong baud rate in Serial Monitor. Set to 115200. |
| Garbled Serial output | Either wrong baud or charge-only USB cable. A charge-only cable will sometimes appear as a COM port but pass nothing usable. |
| No COM port appears | Charge-only USB cable; swap it for a data cable. |
| Student reports exactly 1.0000 Hz | They rounded aggressively when transcribing — have them paste the raw `Frequency: 0.99xx Hz` line they actually saw. The firmware prints to four decimals; nobody will see 1.0000 exactly. |
| Student's answer to Q1 blames the hardware | Gently redirect: "The chip is working correctly. The question is why *correct* software still doesn't produce a *perfect* output." |

## Grading guidance for Q1

Full credit (10 pts) requires recognition of both:
1. `delay()` or software timing isn't perfectly precise
2. The CPU does other things (interrupts, background tasks, system work)

Most students will land somewhere in the 6-9 point range. That's fine — this is the opening step, and the goal is *commitment to a mental model*, not comprehensive understanding. A student who writes "the timing is just slightly off because the CPU does more than just the loop" earns 8 pts cleanly and is well-positioned for Step 2.

Do not penalize informal or casual language. The rubric rewards accurate *understanding*, not polished *writing*.

## Time budget

Budget 12 minutes for this step. Students who finish in under 8 minutes probably rushed the measurement — check that they actually watched 10 cycles and didn't just transcribe the first one. Students who take more than 15 minutes are usually stuck on wiring or USB driver setup; walk around and spot-check.

## Why this opening works

- **Fast hands-on:** students touch hardware within 3 minutes.
- **A surprise they see themselves:** the Serial Monitor reading isn't 1.0000 Hz, and that's weird.
- **A withheld answer:** the explanation exists in the "reveal" block, but only appears after they've committed to a guess.

By the end of Step 1, students are hooked on a small, concrete observation and they've invested a short-answer response in explaining it. That investment is what powers Steps 2-5.

## What not to do

- Do not introduce the word "peripheral" in this step.
- Do not explain the DMA or LEDC peripherals yet — those land in Step 4.
- Do not say "this is about hardware/software co-design." Students will figure that out on their own in Step 4.
- Do not give students the answer before they've written their own. The reveal block is *after* their short-answer submission, not before.

## Required materials (this step only)

- 1 ESP32 DevKit per team
- 1 breadboard per team
- 1 standard LED per team (5 mm, any color)
- 1× 330 Ω resistor per team
- 2 jumper wires per team
- 1 USB **data** cable per team (charge-only cables will not enumerate a COM port)

No oscilloscope is needed. All measurement is via Arduino IDE Serial Monitor.

## Prep checklist for the instructor

- [ ] Confirm `step1_baseline.ino` compiles cleanly with the current arduino-esp32 core before class
- [ ] Confirm at least one spare data-capable USB cable per row of teams (this is the most common day-of failure)
- [ ] Have a canonical Serial Monitor screenshot from `testing_evidence/step1_serial_monitor.png` available to show students if their output looks unexpected
- [ ] Pre-flash one demo ESP32 and have it printing live in Serial Monitor when students walk in — sets the tone immediately
