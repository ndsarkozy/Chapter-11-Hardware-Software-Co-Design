# Chapter 11 Starter Firmware â€” Build & Flash Guide

## Toolchain

| Tool | Required version |
|---|---|
| Arduino IDE | 2.x (2.3.0 or later recommended) |
| arduino-esp32 board package | 3.x (install via Board Manager: `esp32` by Espressif) |
| LiquidCrystal library | built into Arduino IDE (no install needed) |
| PubSubClient library | 2.8.x -- install via Library Manager (Step 4 only) |
| ArduinoJson library | 6.x -- install via Library Manager (Step 4 only) |

> **Board Manager URL:** `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`

## Board settings (Arduino IDE)

| Setting | Value |
|---|---|
| Board | ESP32 Dev Module |
| Upload Speed | 921600 |
| Flash Size | 4MB (32Mb) |
| Partition Scheme | Default 4MB with spiffs |
| Port | whichever COM port your ESP32 appears on |

## Sketches â€” one per lab step

| Step | Folder | What it does |
|---|---|---|
| 1 | `step1_baseline/` | Blinks LED at ~1 Hz, prints measured period to Serial Monitor |
| 2 | `step2_overload/` | Reads potentiometer + drives LCD while CPU load runs; demonstrates software bottleneck |
| 3 | *(no new firmware)* | Use step2 still running; open Serial Monitor to read sample rate |
| 4 | `step4_accelerator/` | Same hardware + same load as Step 2, but ADC via DMA â€” LCD stays smooth |

## Wiring

### Step 1

| Component | ESP32 pin |
|---|---|
| LED anode (via 330 Î© resistor) | GPIO 18 |
| LED cathode | GND |

### Steps 2-4 (identical wiring for both)

LCD is a 16x2 parallel HD44780 module (TC1602A or equivalent), driven in 4-bit mode.

| Component | ESP32 pin / connection |
|---|---|
| Signal pot, middle pin (wiper) | GPIO 34 |
| Signal pot, left outer pin | GND |
| Signal pot, right outer pin | 3.3 V |
| Contrast pot, wiper | LCD V0 (pin 3) |
| Contrast pot, outer pins | 5 V and GND |
| LCD VSS  (pin 1)  | GND |
| LCD VDD  (pin 2)  | 5 V (VIN) |
| LCD V0   (pin 3)  | contrast pot wiper (above) |
| LCD RS   (pin 4)  | GPIO 19 |
| LCD RW   (pin 5)  | GND |
| LCD E    (pin 6)  | GPIO 23 |
| LCD D0-D3 (pins 7-10) | unused (4-bit mode) |
| LCD D4   (pin 11) | GPIO 18 |
| LCD D5   (pin 12) | GPIO 5  |
| LCD D6   (pin 13) | GPIO 17 |
| LCD D7   (pin 14) | GPIO 16 |
| LCD A    (pin 15) | 5 V (through 220 ohm if no built-in resistor) |
| LCD K    (pin 16) | GND |

> If the backlight is on but no characters show, turn the contrast pot. If the backlight is off, check the A-pin wiring.

## Flash procedure

1. Connect ESP32 to laptop via a **data-capable** USB cable (charge-only cables will not show a COM port)
2. Open the sketch folder in Arduino IDE
3. Select the correct board and port under **Tools**
4. Click **Upload** (right-arrow button)
5. If upload fails with a timeout: hold the **BOOT** button on the ESP32 while clicking Upload, release once upload starts
6. Open **Serial Monitor** at **115200 baud** to verify the sketch is running

## Server connection setup (Step 4)

Step 4 firmware (`step4_accelerator.ino`) connects to the classroom server automatically after the DMA pass condition is met. Configuration is at the top of the sketch:

```cpp
#define WIFI_SSID  "CECS"
#define WIFI_PASS  "CECS-Classroom"
#define MQTT_HOST  "192.168.8.10"   // change if server IP changes
#define MQTT_PORT  1883
```

To deploy on a different network, update `MQTT_HOST` and `WIFI_SSID`/`WIFI_PASS` and reflash. The server IP can change if DHCP reassigns it â€” run `ipconfig` on the server laptop to verify before class.

Steps 1â€“3 are fully standalone (no server or WiFi required).

## Common problems

| Problem | Fix |
|---|---|
| No COM port in Arduino IDE | Use a data cable, not a charge-only cable. Try a different USB port. |
| Upload timeout | Hold BOOT button during upload. Some ESP32 boards need this. |
| LCD backlight on, blank screen | Turn the contrast pot. Display is working, contrast just needs adjustment. |
| LCD backlight off | Verify pin 15 (A) wired to 5 V, pin 16 (K) to GND. |
| Random characters or only top row of solid blocks | D4-D7 wiring order swapped. Verify D4=GPIO18, D5=GPIO5, D6=GPIO17, D7=GPIO16. |
| `LiquidCrystal.h` not found | Library is built into Arduino IDE -- if missing, your IDE install is corrupt. Reinstall Arduino IDE. |
| `driver/i2s.h` not found | Wrong board package version â€” must use arduino-esp32 **3.x**. |
| `PubSubClient.h` not found | Install via Library Manager: search "PubSubClient" by Nick O'Leary. |
| `ArduinoJson.h` not found | Install via Library Manager: search "ArduinoJson" by Benoit Blanchon (install v6.x). |
| Step 4: no WiFi connect | Verify SSID/password at top of sketch match the classroom network. |
| Step 4: no MQTT pass sent | Confirm server is running and `MQTT_HOST` IP is correct. Check Serial Monitor for `[MQTT]` lines. |
