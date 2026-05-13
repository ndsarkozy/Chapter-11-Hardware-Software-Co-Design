# Hardware Bill of Materials — Chapter 11

Quantities are **per team of 2 students**. Assume 12 teams per class → multiply by 12 for a full class order. A small overage (10–15%) is wise; students break parts.

## Per-team kit

| Part | Qty per team | Notes | Approx. cost |
|---|---|---|---|
| ESP32 DevKit (38-pin) | 1 | Any common variant (ESP-WROOM-32). USB-C preferred over micro-USB. | $8–12 |
| Solderless breadboard, full-size | 1 | 830 tie-points | $5–7 |
| Jumper wire kit (M-M, M-F) | 1 | 20 of each flavor is plenty | $4–6 |
| Standard 5 mm LED, any color | 2 | Step 1 + 1 spare | $0.10 |
| 330 Ω resistor, 1/4 W | 2 | Step 1 LED current limit + 1 spare | $0.05 |
| Potentiometer, 10 kΩ linear | 2 | One for ADC input on GPIO 34 (signal), one for LCD V0 (contrast) | $1 |
| 16×2 parallel LCD — TC1602A or any HD44780-compatible | 1 | 16-pin parallel module, driven in 4-bit mode | $3–5 |
| 220 Ω resistor, 1/4 W | 1 | LCD backlight current-limit (skip if your module has built-in resistor) | $0.05 |
| USB cable matching the DevKit | 1 | **Data-capable** — charge-only cables will not enumerate a COM port | $2–4 |

**Per-team subtotal:** ~$18–35.

## Shared classroom equipment

| Equipment | Qty per class | Notes |
|---|---|---|
| Mango GL.iNet router (or any AP with WPA2) | 1 | Hosts the local classroom network (`CECS` SSID) for Step 4 MQTT |
| Server laptop | 1 | Runs `START_SERVER.bat`; needs Python 3.10+, Mosquitto, and the `requirements.txt` deps |
| Multimeter | 1–2 | Optional, for debugging miswired LCDs or shorted breadboards |

No oscilloscope, no external power supply, and no scope probes are required. All measurement is via Arduino IDE Serial Monitor at 115200 baud.

## Sourcing notes

- **Adafruit / SparkFun** are the most reliable U.S. sources for ESP32 DevKits and quality LCDs. More expensive but consistent.
- **Amazon / AliExpress** are cheaper if you have time to deal with variation. ESP32 boards especially vary in USB chipset (CH340 vs. CP2102) — buy a test batch first to confirm the driver story before bulk-ordering.
- **Digi-Key / Mouser** for resistors and LEDs in bulk. Much cheaper than Amazon at quantity.

## Per-class estimated cost

~$18–35 per team for the consumable kit. For 12 teams: **~$220–420** for a full class set.

Many parts survive multiple semesters — only LEDs and the occasional resistor or jumper wire need regular replacement. The ESP32, breadboard, potentiometer, LCD, and USB cable should all survive several cycles of use.

## What students keep vs. return

**Return** at end of semester: ESP32 DevKit, breadboard, both potentiometers, LCD module, jumper wire kit.

**Keep** (consumables): resistors, LEDs, USB cable.
