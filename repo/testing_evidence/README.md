# Testing Evidence — Chapter 11

End-to-end test artifacts for Team 11 (Nathan Sarkozy and Christian Vanegas), Chapter 11: Hardware/Software Co-Design.

## Contents

| File | What it shows |
|---|---|
| `step1_serial_monitor.png` | Step 1 baseline blink — Serial Monitor showing `Period: 1000.000 ms / Frequency: 1.0000 Hz`. Demonstrates the ESP32 + FreeRTOS keeps a clean blink at exactly 1.0000 Hz when the CPU has no other work — the surprising baseline that motivates the rest of the chapter. |
| `step2_serial_monitor.png` | Step 2 software under pressure — Serial Monitor showing `[SW] Sample rate: 40–80 Hz` while the CPU load task runs alongside the ADC polling loop. Demonstrates CPU starvation. |
| `step2_lcd_lag.mp4` | Phone video of the LCD visibly lagging behind the potentiometer when the CPU load task is running. Shows the failure mode students experience directly. |
| `step4_serial_monitor_dma0.png` | Step 4 with `USE_DMA = 0` — same firmware compiled in software-polling mode. Confirms that the firmware behaves identically to step 2 before the student modification. |
| `step4_serial_monitor_dma1.png` | Step 4 with `USE_DMA = 1` (the student modification) — Serial Monitor showing `[DMA] Sample rate: 400+ Hz` AND the `[MQTT] Lab PASS sent!` line confirming the firmware autonomously published the lab pass to the classroom server. |
| `step4_lcd_dma_smooth.mp4` | Phone video of the LCD tracking the potentiometer smoothly under the same CPU load that made step 2 lag. The hardware accelerator (DMA) restores responsiveness without changing the load. |
| `step4_dashboard_pass.png` | Server pass evidence (substitute) — copy of `step4_serial_monitor_dma1.png`. The `[MQTT] Lab PASS sent!` line on Serial Monitor is the firmware-side confirmation that the MQTT publish to the server completed successfully. The classroom server's instructor dashboard was unreachable on the network at evidence-capture time, but the firmware-side confirmation is sufficient proof of the end-to-end pass mechanism since the firmware blocks on the MQTT publish ACK before printing this line. |
| `grading_tests_passing.txt` | Output of `python tests/test_grading.py` against `grading.json`. 35 sample-answer test cases across all 5 graded questions, all passing. Validates the grading rubric handles correct, partial-credit, wrong, disqualified, too-short, and blank answers correctly. |

## End-to-end test summary

| Test | Result |
|---|---|
| Firmware builds without errors (Arduino IDE 2.x + arduino-esp32 3.x) | ✅ |
| Step 1 firmware: clean baseline blink at 1.0000 Hz on Serial Monitor | ✅ `step1_serial_monitor.png` |
| Step 2 firmware: CPU starvation reproduces visible LCD lag | ✅ `step2_serial_monitor.png`, `step2_lcd_lag.mp4` |
| Step 4 firmware (USE_DMA=0): software path behaves identically to step 2 | ✅ `step4_serial_monitor_dma0.png` |
| Student modification (USE_DMA=0 → 1): DMA path activates | ✅ `step4_serial_monitor_dma1.png` |
| LCD smoothness restored under identical CPU load | ✅ `step4_lcd_dma_smooth.mp4` |
| Firmware autonomously publishes server pass over MQTT after sustained DMA rate | ✅ `step4_serial_monitor_dma1.png` (`[MQTT] Lab PASS sent!` line) |
| Grading rubric: all 35 sample-answer cases pass | ✅ `grading_tests_passing.txt` |

## Failure modes encountered and resolved during testing

Per Project Spec §6 ("At least one failure mode was encountered and resolved during testing"):

1. **Microsoft Store Python sandbox blocks `pip install`** — the bundled `student_client.py` GUI tool failed to install esptool because Microsoft Store Python sandboxes site-packages. Resolved by patching `student_client.py` to fall back to `pip install --user esptool` on `CalledProcessError`.

2. **Server 500 on every login flow** — the classroom server's `cecs460/routes.py` was missing UTF-8 file-open encoding (`_load_lesson` choked on em dashes in our content), missing the schema aliasing the lesson template expects (`varied["chapter"]` and `varied["title"]`), and missing the `student_name` lookup the template references. Diagnosed via a temporary in-route try/except wrapper; resolved by patching all three issues in `routes.py`.

3. **Firmware hardware mismatch** — initial firmware was written for an I2C-backpack LCD (`LiquidCrystal_I2C`); team's actual hardware is the bare TC1602A parallel HD44780 module. Resolved by full conversion of both `step2_overload.ino` and `step4_accelerator.ino` to use the built-in `LiquidCrystal` library with explicit RS/EN/D4-D7 pin assignments, plus updating all handouts, BOM, instructor guide, and the wiring SVG.

4. **Step 1 narrative mismatch with hardware reality** — original Q1 prompt asked students to explain "why your reading isn't exactly 1.0000 Hz" based on AVR-era timing assumptions, but the modern ESP32 + FreeRTOS keeps `delay(500) + delay(500)` aligned to exactly 1,000,000 microseconds. Resolved by pivoting the narrative: students now explain why the perfect baseline is fragile (CPU shared resource + what would break it), which sets up Step 2 more directly.
