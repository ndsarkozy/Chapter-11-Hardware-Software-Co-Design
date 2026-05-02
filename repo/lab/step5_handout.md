# CECS 460 — Chapter 11 Lab
## Step 5: The Partition Decision

**Time:** ~20 minutes
**You will need:** Your Step 3 and Step 4 sample rate measurements, the lesson system

---

### What you're doing

You've run the full co-design loop: implement in software, measure under load, offload to hardware, measure again. Now you're going to apply that same reasoning to three new scenarios and write your own partitioning rule.

### The decision framework

The rule you derived in Steps 2–4:

1. **Implement in software first** — easier to write, debug, and change
2. **Measure under realistic load** — get a real number
3. **Compare to the requirement** — if software meets it, you're done
4. **Only move to hardware if software demonstrably fails** — and only for the specific function that fails

### Scenario analysis

For each scenario below, decide: **software or hardware?** Write your decision and a one-sentence justification. Reference the decision framework above.

---

**Scenario A:** A temperature sensor is read once every 30 seconds and posted over MQTT. The software read takes ~50 µs.

| | |
|---|---|
| Decision | [ ] Software  [ ] Hardware |
| Justification | |

---

**Scenario B:** An audio codec streams 48,000 16-bit samples per second from a microphone. The CPU must simultaneously run a voice-activity detection algorithm.

| | |
|---|---|
| Decision | [ ] Software  [ ] Hardware (DMA) |
| Justification | |

---

**Scenario C:** An AES-128 encryption key is rotated every 24 hours. Each rotation calls the AES block once.

| | |
|---|---|
| Decision | [ ] Software  [ ] Hardware (AES engine) |
| Justification | |

---

### Your rule

> **Q5 (short answer, graded):** Write your own partitioning decision rule in 2–3 sentences. When should a function move from software to hardware? Use what you observed in Steps 2–4 to support your answer — reference your actual measured sample rates.

Write your answer in the lesson system's Step 5 short-answer box.

---

### Answer key (check your work after submitting)

| Scenario | Answer | Reason |
|---|---|---|
| A | Software | 50 µs once every 30 s is negligible CPU. No hardware needed. |
| B | DMA | 48,000 samples/sec in a polling loop would consume most of the CPU, leaving nothing for detection. Same problem you saw in Step 2, just at audio rates. |
| C | Software | AES once per day is essentially zero CPU. Hardware acceleration is only worth it at high call rates. |

---

### You're done

You've completed Chapter 11. The core takeaway: hardware and software are not opposites — they're partners, and the engineer's job is to decide, based on measurement, where each function lives.
