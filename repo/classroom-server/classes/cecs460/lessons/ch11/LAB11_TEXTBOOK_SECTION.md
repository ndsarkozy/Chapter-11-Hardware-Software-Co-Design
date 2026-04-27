# Lab 11 — Hardware/Software Co-Design: AES Benchmark on the ESP32

## Overview

This lab replaces the open-ended "pick an algorithm" structure with a **single prescribed benchmark** — AES-128 encryption — because it produces the clearest, most comparable measurements across the class and integrates directly with the interactive classroom grading system.

Your ESP32 runs the same 128-bit block through two paths back-to-back:

- **Path A (Software):** A self-contained AES-128 implementation running entirely on the Xtensa CPU core with no hardware assistance.
- **Path B (Hardware):** The same operation routed through the ESP32's dedicated AES hardware engine via the ESP-IDF `esp_aes` driver.

The firmware measures both paths automatically, computes the speedup ratio, and publishes the results to the classroom MQTT server. You then answer a reflection question based on your own device's numbers.

---

## 11.9.1 Objectives

By the end of this lab you will be able to:

1. Implement a software-only AES-128 ECB cipher and measure its execution time on the ESP32.
2. Use the ESP32 hardware AES engine via the `esp_aes` driver and measure its execution time.
3. Calculate speedup and CPU utilization headroom for a given packet rate.
4. Apply the "start in software" heuristic to a real measured result.
5. Identify the data-movement overhead in the hardware path (setup, key schedule, output copy).
6. Publish structured telemetry to an MQTT broker and have it graded automatically.

---

## 11.9.2 Hardware and Software Requirements

| Item | Requirement |
|------|-------------|
| Board | ESP32 DevKit-C (Xtensa LX6) |
| Framework | Arduino-ESP32 (via Arduino IDE or PlatformIO) |
| Libraries | `PubSubClient`, `ArduinoJson`, `Preferences` (all standard with Arduino-ESP32) |
| ESP-IDF header | `esp_aes.h` — included automatically with Arduino-ESP32 |
| Network | Classroom Wi-Fi + MQTT broker on instructor laptop |

No external hardware is required. No additional libraries beyond the standard Arduino-ESP32 install.

---

## 11.9.3 What the Firmware Does Automatically

The provided firmware (`CECS460_Lab11_AES.ino`) performs the following sequence with no student interaction after flashing:

1. Connects to the classroom Wi-Fi and MQTT broker.
2. Waits for slot assignment from the server (same MAC-based system as all other labs).
3. Runs **1,000 iterations** of software AES-128 ECB on a fixed 16-byte plaintext block, measuring total time with `esp_timer_get_time()`. Records average µs per block.
4. Runs **1,000 iterations** of hardware AES-128 ECB on the same block. Records average µs per block.
5. Computes speedup = `sw_us / hw_us`.
6. Publishes a continuous telemetry stream to `c460_ch11_codesign/{slot}/bench` every 10 seconds so the instructor dashboard shows live results.
7. Submits the structured answer string `[hw:sw_us=X hw_us=Y speedup=Z blocks=1000]` to the lesson answer topic, which the grading engine scores automatically.

The serial monitor shows every step in detail so students can follow the benchmark execution and verify the numbers.

---

## 11.9.4 Benchmark Measurement Method

Both paths use `esp_timer_get_time()` — a 64-bit microsecond timer driven by the ESP32's internal clock. The sequence for each path is:

```
t_start = esp_timer_get_time()
for i in 0..N:
    aes_encrypt_block(key, plaintext, ciphertext)
t_end = esp_timer_get_time()
avg_us = (t_end - t_start) / N
```

The loop runs N=1000 iterations to average out interrupt jitter and cache warm-up effects. The first 10 iterations are discarded as a warm-up phase.

**What is included in the hardware path timing:**
- `esp_aes_setkey()` call (once, outside the loop)
- `esp_aes_crypt_ecb()` call (inside the loop)
- Output copy from hardware result buffer to local variable

**What is NOT included:**
- Network I/O
- MQTT publish
- Serial print

This gives a fair comparison of the pure computation path in each case.

---

## 11.9.5 Part 1 — Observe and Record

Flash the firmware and open the Serial Monitor at 115200 baud. You will see output like:

```
╔══════════════════════════════════════╗
║  CECS 460 Lab 11 — AES Benchmark     ║
╚══════════════════════════════════════╝
[Boot] MAC: AABBCCDDEEFF  Device: esp32_DDEEFF
[WiFi] Connecting to CECS...
[WiFi] Connected! IP: 192.168.8.42  RSSI: -62 dBm
[MQTT] Connected
[ASSIGN] Slot: 7  Token: a3f9
[AES-SW]  Warming up...
[AES-SW]  1000 blocks: 312450 µs total → 312 µs/block
[AES-HW]  Warming up...
[AES-HW]  1000 blocks: 3210 µs total → 3 µs/block
[RESULT]  Speedup: 104x
[MQTT]    Answer submitted: [hw:sw_us=312 hw_us=3 speedup=104 blocks=1000]
```

Record your numbers:

| Measurement | Your value |
|-------------|------------|
| SW AES avg (µs/block) | ________ |
| HW AES avg (µs/block) | ________ |
| Speedup ratio | ________ |

---

## 11.9.6 Part 2 — Analysis Questions (Submitted via Serial)

After the benchmark completes, the serial prompt accepts your typed reflection answer. Type your response and press Enter — it is published to the classroom server as your `q_lab2` answer.

**Reflection question:**

> "Your measured speedup for AES-128 is approximately **{your speedup}×**. Based on this result and the start-in-software heuristic, at what packet rate (packets/second) would using the hardware AES engine become justified for a battery-powered IoT device? Show your reasoning using your measured numbers. Then name one *additional* overhead cost that your benchmark does not capture but would matter in a production firmware."

Your answer should include:
- A specific packet rate threshold with a calculation
- The CPU% headroom argument
- One real overhead not captured by the isolated benchmark (e.g., DMA setup, key management, interrupt latency, buffer copy cost)

---

## 11.9.7 Part 3 — Class Comparison

The instructor dashboard shows every slot's `sw_us`, `hw_us`, and `speedup` in real time. After all devices have reported:

- What is the range of SW AES times across the class? What explains device-to-device variation?
- Does every device show the same HW AES time? Why or why not?
- Is the speedup ratio consistent, or does it vary? What does variation in speedup tell you?

Discuss these questions as a class. The instructor will display the live distribution chart.

---

## 11.9.8 Part 4 — Co-Design Reflection (Written, Ungraded)

In your lab report, address the following:

1. **Partitioning decision:** If you were designing a smart lock that encrypts one AES block every time a credential is verified (at most 5 verifications per second), would you use the software or hardware AES path? Show the CPU% calculation to support your answer.

2. **Hidden overhead:** The benchmark loop only measures `esp_aes_crypt_ecb()`. In production firmware, what additional steps surround each AES call, and how would you measure their cost?

3. **The over-optimistic accelerator pitfall:** Suppose a student designs a custom AES accelerator on an FPGA that processes a block in 1 µs, but the SPI interface to the FPGA adds 50 µs of transfer overhead per block. Compared to the ESP32's hardware AES engine (3 µs with zero transfer overhead), which is faster in practice? What design lesson does this illustrate?

4. **Software-appropriate functions:** The ESP32 hardware AES engine is fast and energy-efficient. Name two functions in a real IoT product that should still remain in firmware even though hardware implementation is possible, and explain why using the tape-out economics argument from Section 11.2.

---

## 11.9.9 Grading

| Component | Points | How graded |
|-----------|--------|------------|
| `q_lab1` — AES benchmark telemetry | 10 | Automatic: server validates `sw_us`, `hw_us`, `speedup` are in plausible ranges and `hw_us < sw_us` |
| `q_lab2` — Reflection answer | 10 | Keyword scoring (immediate) + AI rubric review (post-session) |
| `q1`–`q4` — Lecture questions | 80 | Keyword scoring + AI rubric review |

The benchmark result is graded automatically the moment your device publishes it. The reflection answer uses the same keyword engine as all other chapter questions. Both are visible on the instructor dashboard in real time.
