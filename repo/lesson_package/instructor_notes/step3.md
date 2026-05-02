# Instructor Notes — Step 3: Why Did It Fail?

## What this step demonstrates
Quantifying a failure: students read the sample rate from Serial Monitor and compare it to a hypothetical 50 Hz requirement. The goal is to establish the habit of measuring before fixing — not just observing that something is slow.

## No new firmware needed
Step 3 uses the same `step2_overload.ino` firmware. No reflash required. Instructor tells students "keep the Step 2 firmware running and read the Serial Monitor."

## Expected observations
- `[SW] Sample rate:` values: **40–80 Hz** depending on hardware and load strength
- The hypothetical 50 Hz requirement is not met at the lower end of this range
- Students fill in their measured value in the handout table

## Discussion prompt
Ask students: "What would happen in a real temperature controller if it sampled at 40 Hz instead of 50 Hz?" Expected answer: the controller might miss a peak temperature spike — the reading it acts on is 25 ms stale. In a fast thermal runaway, that matters.

## Graded question
Q3 (`q3_diagnose`): asks students to interpret the sample rate and explain what happens if it misses a 50 Hz requirement. Full credit requires: (1) rate meaning (how many ADC reads/second), (2) system fails its deadline if measured rate < requirement, (3) a real-world consequence (stale data, missed safety threshold, broken control loop). Partial credit for (1) + (2) without (3).

## Timing note
This step takes 5–10 minutes. Students with faster hardware may see rates near 80 Hz and argue they meet 50 Hz. That is fine — the point is the methodology (measure → compare → conclude), not the specific number.
