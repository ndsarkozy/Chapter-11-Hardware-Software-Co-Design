# Instructor Notes — Step 2: Software Under Pressure

## What this step demonstrates
CPU contention: the software polling loop and the CPU load task share one core. As `LOAD_STRENGTH` increases, the ADC read gets starved and the LCD visibly lags behind the knob. Students experience the failure directly before being asked to explain it.

## Expected observations
- LCD knob readout: visibly sluggish (updates 1–4× per second despite fast knob movement)
- Serial Monitor `[SW] Sample rate:` lines: expect **40–80 Hz** at `LOAD_STRENGTH = 5000`
- LCD bottom row: `SW Poll  LAGGING`

## Common issues
| Symptom | Likely cause | Fix |
|---|---|---|
| LCD backlight on, blank screen | Contrast not adjusted | Turn the contrast pot (V0) until characters appear |
| LCD backlight off | A-pin wiring | Verify pin 15 (A) → 5 V (through 220 Ω if no built-in resistor), pin 16 (K) → GND |
| Random characters or only top row of solid blocks | D4–D7 swapped | Verify D4=GPIO 18, D5=GPIO 5, D6=GPIO 17, D7=GPIO 16 |
| No Serial output | Wrong baud rate in Serial Monitor | Set to 115200 |
| Sample rate looks high (~1000 Hz) | `LOAD_STRENGTH` too low | Increase to 10000–50000 to make the lag more pronounced |
| Sample rate looks too low (<10 Hz) | `LOAD_STRENGTH` too high | Reduce to 1000–2000 |

## Tuning the demo
`#define LOAD_STRENGTH 5000` produces ~40–80 Hz, which creates visible lag without freezing the LCD entirely. For a larger classroom display, increase to 20000 for a more dramatic effect.

## Graded question
Q2 (`q2_why_lag`): asks students to explain in 2–3 sentences why the load causes lag. Full credit requires: (1) CPU is a shared resource, (2) load task occupies CPU so ADC read waits, (3) result is lag/stale display. Common partial-credit answer: "the CPU is busy" — correct but lacks the mechanism.
