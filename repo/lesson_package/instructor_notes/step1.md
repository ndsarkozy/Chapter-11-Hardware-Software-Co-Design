# Instructor notes — Step 1: A blink that almost works

## Step intent

The opening step has one job: **get students to commit to a mental model about why software timing isn't perfect, without naming the concept yet.** Everything else in this lesson depends on them having invested in this first question.

Do not front-load vocabulary. Words like "partitioning," "peripheral," "co-design," and "offload" should not appear in your introduction to Step 1. They appear naturally in Step 3 and Step 4 as labels for things students have already felt.

## Expected student measurements

Students will measure frequencies roughly in the range **0.996 to 1.004 Hz**. The dominant source of drift is the Arduino core's RTOS tick and the handful of microseconds `delay()` rounds against the tick period. The exact number varies per board — crystal tolerance, temperature, and WiFi/BT radio state all contribute. **This is a feature, not a bug.** Every student's scope reads a slightly different number, which makes copying meaningless and drives genuine engagement with the question.

If a student reports a frequency wildly outside this range (< 0.9 or > 1.1), something is wrong — most likely the scope trigger is picking up noise, or they're measuring the wrong channel.

## Common student mistakes

| Mistake | What to do |
|---|---|
| LED doesn't light up | Check polarity (anode to GPIO side, cathode to GND). Check that the sketch actually compiled and uploaded — look for "Hard resetting via RTS pin..." in the upload log. |
| LED lights but scope shows DC | Trigger not set up correctly. Students often forget to set trigger source to CH1. |
| Scope reports 500 mHz or 2 Hz | They're measuring period-of-period or half-period. Use auto-measure "Frequency," not "Pulse Width." |
| Student reports exactly 1.0000 Hz | Either (a) they rounded aggressively, (b) the scope's resolution is too coarse — have them zoom in on timebase to 100 ms/div and remeasure, or (c) the scope is averaging heavily and they need to disable it. |
| Student's answer to Q1 blames the hardware | Gently redirect: "The chip is working correctly. The question is why *correct* software still doesn't produce a *perfect* output." |

## Grading guidance for Q1

Full credit (10 pts) requires recognition of both:
1. `delay()` or software timing isn't perfectly precise
2. The CPU does other things (interrupts, background tasks, system work)

Most students will land somewhere in the 6-9 point range. That's fine — this is the opening step, and the goal is *commitment to a mental model*, not comprehensive understanding. A student who writes "the timing is just slightly off because the CPU does more than just the loop" earns 8 pts cleanly and is well-positioned for Step 2.

Do not penalize informal or casual language. The rubric rewards accurate *understanding*, not polished *writing*.

## Time budget

Budget 12 minutes for this step. Students who finish in under 8 minutes probably rushed the measurement — check that their scope reading is plausible. Students who take more than 15 minutes are usually stuck on wiring or scope setup; walk around and spot-check.

## Why this opening works

- **Fast hands-on:** students touch hardware within 3 minutes.
- **A surprise they see themselves:** the scope reading isn't 1.0000 Hz, and that's weird.
- **A withheld answer:** the explanation exists in the "reveal" block, but only appears after they've committed to a guess.

By the end of Step 1, students are hooked on a small, concrete observation and they've invested a short-answer response in explaining it. That investment is what powers Steps 2-5.

## What not to do

- Do not introduce the word "peripheral" in this step.
- Do not explain the RMT or LEDC peripherals yet.
- Do not say "this is about hardware/software co-design." Students will figure that out on their own in Step 4.
- Do not give students the answer before they've written their own. The reveal block is *after* their short-answer submission, not before.

## Required materials (this step only)

- 1 ESP32 DevKit per team
- 1 breadboard per team
- 1 standard LED per team (5 mm, any color)
- 1x 330 Ω resistor per team
- 2 jumper wires per team
- 1 oscilloscope (shared is fine; budget ~5 minutes of scope time per team)

## Prep checklist for the instructor

- [ ] Confirm `step1_baseline.ino` compiles cleanly with the current arduino-esp32 core before class
- [ ] Confirm at least one working scope per 2-3 teams
- [ ] Have the canonical scope capture (`testing_evidence/step1_canonical_scope.png`) available to show students if a scope is misbehaving and you need a reference
- [ ] Pre-wire one demo board and have it measuring live on a demo scope when students walk in — it sets the tone immediately
