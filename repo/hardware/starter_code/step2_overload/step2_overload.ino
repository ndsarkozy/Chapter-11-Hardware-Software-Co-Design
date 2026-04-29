/*
 * Step 2 — Software Under Pressure
 * CECS 460 Chapter 11: Hardware/Software Co-Design
 *
 * Potentiometer on GPIO 34 → ADC read in software loop
 * LCD 16x2 (I2C) displays the live ADC value
 * Background CPU load task runs simultaneously
 *
 * Expected result: LCD updates become slow and unresponsive
 * as the CPU load increases — the software cannot do both at once.
 *
 * Hardware:
 *   LCD I2C: SDA → GPIO 21, SCL → GPIO 22, VCC → 5V, GND → GND
 *   Potentiometer: middle pin → GPIO 34, outer pins → 3.3V and GND
 */

#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define POT_PIN       34
#define LOAD_STRENGTH 5000    // iterations of fake work per loop — increase to make it worse
#define SAMPLE_PRINT_MS 500   // how often to print sample rate to Serial

LiquidCrystal_I2C lcd(0x27, 16, 2);

// ── CPU load task ────────────────────────────────────────────────────────────
// Simulates a busy processing task hogging the CPU
volatile float g_load_result = 0;

void runCpuLoad() {
  float x = 1.0;
  for (int i = 0; i < LOAD_STRENGTH; i++) {
    x = x * 1.0001f + 0.0001f;  // busy math the compiler won't optimize away
  }
  g_load_result = x;
}

// ── Sampling rate tracker ────────────────────────────────────────────────────
unsigned long g_sampleCount = 0;
unsigned long g_lastPrintMs = 0;

void setup() {
  Serial.begin(115200);

  Wire.begin(21, 22);
  lcd.init();
  lcd.backlight();

  lcd.setCursor(0, 0);
  lcd.print("CECS 460 Step 2");
  lcd.setCursor(0, 1);
  lcd.print("SW Under Pressure");
  delay(2000);
  lcd.clear();

  Serial.println("=== Step 2: Software Under Pressure ===");
  Serial.println("Turn the potentiometer and watch the LCD lag.");
  Serial.println("Sample rate printed every 500ms.");
}

void loop() {
  // ── CPU load — runs every loop iteration, starving the ADC read ──────────
  runCpuLoad();

  // ── Software ADC read ────────────────────────────────────────────────────
  int raw = analogRead(POT_PIN);          // 0–4095
  int percent = map(raw, 0, 4095, 0, 100);
  g_sampleCount++;

  // ── Update LCD ───────────────────────────────────────────────────────────
  lcd.setCursor(0, 0);
  lcd.print("Knob:           ");
  lcd.setCursor(6, 0);
  lcd.print(percent);
  lcd.print("%   ");

  lcd.setCursor(0, 1);
  lcd.print("SW Poll  LAGGING");

  // ── Print sample rate to Serial ──────────────────────────────────────────
  unsigned long now = millis();
  if (now - g_lastPrintMs >= SAMPLE_PRINT_MS) {
    unsigned long elapsed = now - g_lastPrintMs;
    float rate = (float)g_sampleCount / (elapsed / 1000.0f);
    Serial.print("[SW] Sample rate: ");
    Serial.print(rate, 1);
    Serial.print(" Hz  |  Knob: ");
    Serial.print(percent);
    Serial.println("%");
    g_sampleCount = 0;
    g_lastPrintMs = now;
  }
}
