# Chapter 11 Starter Firmware — Build & Flash Guide

## Toolchain

| Tool | Required version |
|---|---|
| Arduino IDE | 2.x (2.3.0 or later recommended) |
| arduino-esp32 board package | 3.x (install via Board Manager: `esp32` by Espressif) |
| LiquidCrystal_I2C library | Any version — install via Library Manager |
| PubSubClient library | 2.8.x — install via Library Manager (Step 4 only) |
| ArduinoJson library | 6.x — install via Library Manager (Step 4 only) |

> **Board Manager URL:** `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`

## Board settings (Arduino IDE)

| Setting | Value |
|---|---|
| Board | ESP32 Dev Module |
| Upload Speed | 921600 |
| Flash Size | 4MB (32Mb) |
| Partition Scheme | Default 4MB with spiffs |
| Port | whichever COM port your ESP32 appears on |

## Sketches — one per lab step

| Step | Folder | What it does |
|---|---|---|
| 1 | `step1_baseline/` | Blinks LED at ~1 Hz, prints measured period to Serial Monitor |
| 2 | `step2_overload/` | Reads potentiometer + drives LCD while CPU load runs; demonstrates software bottleneck |
| 3 | *(no new firmware)* | Use step2 still running; open Serial Monitor to read sample rate |
| 4 | `step4_accelerator/` | Same hardware + same load as Step 2, but ADC via DMA — LCD stays smooth |

## Wiring

### Step 1

| Component | ESP32 pin |
|---|---|
| LED anode (via 330 Ω resistor) | GPIO 18 |
| LED cathode | GND |

### Steps 2–4 (identical wiring for both)

| Component | ESP32 pin |
|---|---|
| Potentiometer middle pin (wiper) | GPIO 34 |
| Potentiometer left outer pin | GND |
| Potentiometer right outer pin | 3.3 V |
| LCD SDA | GPIO 21 |
| LCD SCL | GPIO 22 |
| LCD VCC | 5 V (VIN) |
| LCD GND | GND |

> LCD I2C address assumed: **0x27**. If the LCD stays blank, try `0x3F` and update line 24 in the sketch.

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
#define WIFI_SSID  "DEEZ"
#define WIFI_PASS  "password"
#define MQTT_HOST  "192.168.8.228"   // change if server IP changes
#define MQTT_PORT  1883
```

To deploy on a different network, update `MQTT_HOST` and `WIFI_SSID`/`WIFI_PASS` and reflash. The server IP can change if DHCP reassigns it — run `ipconfig` on the server laptop to verify before class.

Steps 1–3 are fully standalone (no server or WiFi required).

## Common problems

| Problem | Fix |
|---|---|
| No COM port in Arduino IDE | Use a data cable, not a charge-only cable. Try a different USB port. |
| Upload timeout | Hold BOOT button during upload. Some ESP32 boards need this. |
| LCD blank after flash | Check I2C address (try 0x3F). Check 5 V wiring to LCD VCC. |
| LCD shows garbage | Wrong baud rate in Serial Monitor, or I2C address mismatch. |
| `LiquidCrystal_I2C` not found | Install via Library Manager: search "LiquidCrystal I2C" by Frank de Brabander. |
| `driver/i2s.h` not found | Wrong board package version — must use arduino-esp32 **3.x**. |
| `PubSubClient.h` not found | Install via Library Manager: search "PubSubClient" by Nick O'Leary. |
| `ArduinoJson.h` not found | Install via Library Manager: search "ArduinoJson" by Benoit Blanchon (install v6.x). |
| Step 4: no WiFi connect | Verify SSID/password at top of sketch match the classroom network. |
| Step 4: no MQTT pass sent | Confirm server is running and `MQTT_HOST` IP is correct. Check Serial Monitor for `[MQTT]` lines. |
