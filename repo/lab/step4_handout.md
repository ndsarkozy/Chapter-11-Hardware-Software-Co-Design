# CECS 460 — Chapter 11 Lab
## Step 4: The Accelerator

**Time:** ~25 minutes
**You will need:** Same hardware as Steps 2–3 (no changes), USB data cable

---

### What you're doing

You're going to modify one line of the firmware to switch from software ADC polling to hardware DMA acceleration — on the exact same hardware, with the exact same CPU load still running. Then you'll observe the difference and let the server record your pass automatically.

### Do not change any wiring

The circuit is identical to Steps 2 and 3. Potentiometer still on GPIO 34, LCD still on GPIO 21/22.

---

### Your firmware modification

Open `hardware/starter_code/step4_accelerator/step4_accelerator.ino`.

Near the top of the file you will find:

```cpp
// ── STUDENT TASK ─────────────────────────────────────────────────────────────
#define USE_DMA  0   // ← CHANGE THIS TO 1 TO ENABLE DMA ACCELERATION
```

**Change the `0` to `1`.** That single line switches the firmware from:
- `USE_DMA = 0`: software `analogRead()` loop — the same slow approach as Step 2
- `USE_DMA = 1`: ESP32 DMA controller fills ADC buffer at 10,000 samples/sec, CPU just reads the buffer

Save the file, then upload it to your ESP32.

---

### What you should see

**With USE_DMA = 0 (before your change):**
- LCD bottom row: `SW Poll  LAGGING`
- LCD knob display: sluggish, same lag as Step 2
- Serial Monitor: `[SW]  Sample rate: ~40–80 Hz`

**With USE_DMA = 1 (after your change):**
- LCD briefly shows `Step4: DMA Mode`, then switches to live knob display
- LCD bottom row: `DMA      SMOOTH`
- LCD knob display: responds instantly — no lag even with CPU load running
- Serial Monitor: `[DMA] Sample rate: ~400–500 Hz`

Turn the potentiometer. It should track the knob without visible lag.

---

### Measure the improvement

Open **Serial Monitor** (Tools → Serial Monitor, baud **115200**).

With USE_DMA=1 you will see lines like:

```
[DMA] Sample rate: 428.6 Hz  |  Knob: 52%  [pass check: 2s/5s]
[DMA] Sample rate: 431.2 Hz  |  Knob: 53%  [pass check: 3s/5s]
[DMA] Sample rate: 429.8 Hz  |  Knob: 54%  [pass check: 4s/5s]
[DMA] Sample rate: 427.5 Hz  |  Knob: 51%  [pass check: 5s/5s]
[MQTT] Lab PASS sent! DMA rate was 427.5 Hz
```

Watch it for 30 seconds and record a representative value.

| | Step 3 (SW) | Step 4 (DMA) |
|---|---|---|
| Sample rate (Hz) | __________ | __________ |
| Meets 50 Hz requirement? | [ ] Yes  [ ] No | [ ] Yes  [ ] No |
| Approximate improvement factor | — | __________ × faster |

---

### Server pass

Once your DMA sample rate holds above 200 Hz for 5 seconds, the firmware automatically connects to the classroom WiFi and reports your lab pass to the server. You will see on the LCD: `DMA PASS SENT!`

The instructor dashboard will show your slot as passing this step. **You do not need to do anything manually — the firmware handles it.**

If you don't see the pass message after 30 seconds with USE_DMA=1:
- Check that you are connected to the `DEEZ` WiFi network
- Check that the classroom server is running (ask your instructor)
- Verify you actually changed `USE_DMA 0` to `USE_DMA 1` and reflashed

---

### What DMA is doing differently

In Step 2, the CPU called `analogRead()` inside the loop — which meant:
1. CPU stops load task
2. CPU triggers ADC conversion
3. CPU waits for result
4. CPU stores result
5. CPU goes back to load task

In Step 4, the ESP32's DMA controller is configured to sample GPIO 34 at 10,000 times per second completely on its own. The CPU only reads the already-filled buffer when it needs a value. Steps 1–4 above are handled entirely in hardware with no CPU involvement.

---

### Think about it

> **Q4 (short answer, graded):** Compare your Step 3 and Step 4 sample rates. In 2–3 sentences, explain what the DMA controller did differently from the software polling loop. Why did offloading to DMA fix the problem without changing the CPU load at all?

Write your answer in the lesson system's Step 4 short-answer box.

---

### What's next

You've seen the failure and the fix. Step 5 asks you to generalize: given a new system and new requirements, how do you decide where to draw the hardware/software line?
