# CECS 460 — Chapter 11 Lab
## Step 4: The Accelerator

**Time:** ~20 minutes
**You will need:** Same hardware as Steps 2–3 (no changes), USB data cable

---

### What you're doing

You're going to flash different firmware onto the exact same hardware with the exact same CPU load running — and watch the problem disappear. The only change is how the ADC sampling is done: instead of the CPU polling, a dedicated DMA controller handles it.

### Do not change any wiring

The circuit is identical to Steps 2 and 3. Potentiometer still on GPIO 34, LCD still on GPIO 21/22.

### Flash it

Open `hardware/starter_code/step4_accelerator/step4_accelerator.ino` and upload it to your ESP32.

The LCD will briefly show "DMA Accelerator", then start displaying the knob percentage again. The bottom row now reads **`DMA      SMOOTH`**.

### Observe the difference

Turn the potentiometer. The LCD should track the knob without visible lag — even though the same CPU load task is still running.

| Observation | Step 2 | Step 4 |
|---|---|---|
| LCD response to knob | Lagging | __________ |
| Bottom LCD row | SW Poll  LAGGING | __________ |

### Measure the improvement

Open **Serial Monitor** (Tools → Serial Monitor, baud **115200**).

You will now see `[DMA]` lines:

```
[DMA] Sample rate: 428.6 Hz  |  Knob: 52%
[DMA] Sample rate: 431.2 Hz  |  Knob: 53%
```

Watch it for 30 seconds and record a representative value.

| | Step 3 (SW) | Step 4 (DMA) |
|---|---|---|
| Sample rate (Hz) | __________ | __________ |
| Meets 50 Hz requirement? | [ ] Yes  [ ] No | [ ] Yes  [ ] No |
| Approximate improvement factor | — | __________ × faster |

### What DMA is doing differently

In Step 2, the CPU called `analogRead()` inside the loop — which meant:
1. CPU stops what it's doing
2. CPU triggers ADC conversion
3. CPU waits for result
4. CPU stores result
5. CPU goes back to load task

In Step 4, the ESP32's DMA controller is configured to sample GPIO 34 at 10,000 times per second completely on its own. The CPU only reads the already-filled buffer when it needs a value. Steps 1–4 above are handled entirely in hardware with no CPU involvement.

### Think about it

> **Q4 (short answer, graded):** Compare your Step 3 and Step 4 sample rates. In 2–3 sentences, explain what the DMA controller did differently from the software polling loop. Why did offloading to DMA fix the problem without changing the CPU load at all?

Write your answer in the lesson system's Step 4 short-answer box.

### What's next

You've seen the failure and the fix. Step 5 asks you to generalize: given a new system and new requirements, how do you decide where to draw the hardware/software line?
