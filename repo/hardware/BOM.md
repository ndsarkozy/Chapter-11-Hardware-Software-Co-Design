# Hardware Bill of Materials — Chapter 11

Quantities are **per team of 2 students**. Assume 12 teams per class → multiply by 12 for a full class order. A small overage (10-15%) is wise; students break parts.

## Core parts

| Part | Qty per team | Notes | Approx. cost |
|---|---|---|---|
| ESP32 DevKit (38-pin) | 1 | Any common variant (ESP-WROOM-32). USB-C preferred over micro-USB. | $8-12 |
| Solderless breadboard, full-size | 1 | 830 tie-points | $5-7 |
| Jumper wire kit (M-M, M-F, F-F) | 1 | 40 of each flavor is plenty | $6-8 |
| Standard 5 mm LED, any color | 2 | One for Step 1, one spare | $0.10 |
| 330 Ω resistor, 1/4 W | 2 | Step 1 LED current limit + spare | $0.05 |
| 470 Ω resistor, 1/4 W | 1 | WS2812 data-line series resistor | $0.05 |
| 1000 μF electrolytic capacitor, 10 V+ | 1 | WS2812 power-rail smoothing | $0.30 |
| WS2812B LED strip, 16 pixels | 1 | 5 V strip; pre-soldered pigtails preferred. Sold as "NeoPixel" or "WS2812B 60/m" cut to 16 LEDs. | $4-6 |
| Tactile pushbutton, through-hole | 1 | 4-pin, 6 mm body | $0.20 |
| 10 kΩ resistor, 1/4 W | 1 | Pull-down for button | $0.05 |
| USB cable (type matching your DevKit) | 1 | Data cable, not charge-only | $2-4 |

## Shared classroom equipment

| Equipment | Qty per class | Notes |
|---|---|---|
| Oscilloscope, 2ch, 20 MHz+ | 4-6 | Ideally one per 2-3 teams. Rigol DS1054Z or similar. |
| Scope probes, 1x/10x switchable | 8-12 | Two per scope |
| External 5 V power supply | 2-3 | 2A+ recommended for the WS2812 strips; USB power bank works too |
| Multimeter | 2-3 | For debugging-only, not required per team |

## Sourcing notes

- **Adafruit / SparkFun** are the most reliable U.S. sources for NeoPixel strips and ESP32 DevKits. More expensive but quality is consistent.
- **Amazon / AliExpress** are cheaper if you have time to deal with variation. ESP32 boards especially vary in USB chipset (CH340 vs. CP2102) — buy a test batch first.
- **Digi-Key / Mouser** for resistors, capacitors, and buttons. Much cheaper than Amazon in bulk.

## Per-class estimated cost

~$25-35 per team for consumable parts (excluding the scope, which the lab already has).
For 12 teams: **~$300-400** in new parts per offering of the course.

Many parts are reusable between semesters — only LEDs, capacitors, and occasionally resistors need regular replacement.

## What students keep vs. return

**Return** at end of semester: ESP32 DevKit, breadboard, WS2812 strip, jumper wire kit, oscilloscope probes.

**Keep** (consumables): resistors, LEDs, capacitor, button, USB cable.
