# Instructor Notes â€” Step 4: The Accelerator

## What this step demonstrates
Hardware offload: the ESP32's DMA controller samples the ADC at 10 kHz autonomously. The same CPU load from Step 2 still runs â€” but now it doesn't affect the sample rate because DMA and CPU operate in parallel on separate hardware.

## Student modification task
Students must change `#define USE_DMA 0` to `#define USE_DMA 1` near the top of `step4_accelerator.ino`, then reflash. This is the required firmware modification the spec demands. The change:
- Compiles in the I2S DMA driver (`driver/i2s.h`, `driver/adc.h`)
- Calls `setupDmaAdc()` in `setup()`
- Replaces `analogRead()` with `readDmaAdc()` in `loop()`

## Expected observations after student change
- LCD bottom row: `DMA      SMOOTH` (instead of LAGGING)
- Serial Monitor: `[DMA] Sample rate: 400â€“500 Hz` (was 40â€“80 Hz)
- LCD knob response: immediate â€” no visible lag

## Server pass
The firmware connects to WiFi (`CECS`/`CECS-Classroom`) and MQTT (`192.168.8.10:1883`). When the DMA sample rate holds above 200 Hz for 5 seconds, it publishes a pass to `c460_ch11_codesign/{slot}/answer` targeting the `ch11Lab` grading chapter. The instructor dashboard will show the slot pass status.

**If students don't see `DMA PASS SENT!` on the LCD:**
1. Confirm they are on `CECS` WiFi (ESP32 connects automatically)
2. Confirm the classroom server is running (`START_SERVER.bat`)
3. Check Serial Monitor for `[MQTT] Connecting...` or `[MQTT] Connected` messages
4. If MQTT host is wrong: update `#define MQTT_HOST` and reflash

## Required libraries
- `LiquidCrystal` -- built into Arduino IDE (no install needed)
- `PubSubClient` (Nick O'Leary) -- Library Manager, v2.8.x
- `ArduinoJson` (Benoit Blanchon) -- Library Manager, v6.x (NOT v7)

## Graded question
Q4 (`q4_accelerator`): compare Step 3 and Step 4 sample rates, explain what DMA did differently. Full credit requires: (1) DMA autonomous/no CPU, (2) DMA and CPU run in parallel, (3) rate improved. The most common partial-credit answer covers (1) but not (2): "DMA handles ADC so CPU doesn't have to." Correct but misses the parallel execution insight.
