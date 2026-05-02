# CECS 460 — Chapter 11 Lab
## Step 3: Why Did It Fail?

**Time:** ~15 minutes
**You will need:** Step 2 still running (do not reflash), Serial Monitor open

---

### What you're doing

The step2_overload firmware is still running. It's already printing ADC sample rate data to Serial Monitor every 500 ms. You're going to read that number carefully and understand what it means as a system requirement.

### Read the data

Serial Monitor should still be open from Step 2. If not, reopen it at **115200 baud**.

You should see lines printing every half-second:

```
[SW] Sample rate: 42.3 Hz  |  Knob: 67%
```

Let it run for at least 30 seconds to get a stable average. The number will vary slightly — that's normal.

| My measurement | |
|---|---|
| Software ADC sample rate (Hz) | __________ |

*(This should match what you recorded in Step 2. If it's very different, check that you haven't reflashed.)*

### What the number means

Imagine this potentiometer was a real sensor with a hard requirement: **the system must read it at least 50 times per second** (50 Hz) to maintain accuracy.

Fill in the table:

| | Value |
|---|---|
| Required sample rate | 50 Hz |
| Your measured sample rate | __________ Hz |
| Does software meet the requirement? | [ ] Yes  [ ] No |
| By how much does it miss (or exceed)? | __________ Hz |

### Think about it

> **Q3 (short answer, graded):** The sample rate you measured tells you how often the CPU managed to read the ADC. In 2–3 sentences, explain what this number means for the system. If this were a real sensor (e.g., reading temperature 50 times per second is required), what would happen?

Write your answer in the lesson system's Step 3 short-answer box.

### What's next

You now have a concrete failure number. In Step 4, you'll flash the DMA version, run the exact same CPU load, and measure again. Keep this number — you'll need it for comparison.
