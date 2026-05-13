/*
 * Step 2 -- Software Under Pressure
 * CECS 460 Chapter 11: Hardware/Software Co-Design
 *
 * Potentiometer on GPIO 34 -> ADC read in software loop
 * 16x2 parallel HD44780 LCD (TC1602A) displays the live ADC value
 * Background CPU load task runs simultaneously
 *
 * Expected result: LCD updates become slow and unresponsive
 * as the CPU load increases -- the software cannot do both at once.
 *
 * Hardware (TC1602A parallel LCD, 4-bit mode):
 *   LCD VSS  -> GND
 *   LCD VDD  -> 5V
 *   LCD V0   -> wiper of contrast pot (10k); pot outer pins to 5V and GND
 *   LCD RS   -> GPIO 19
 *   LCD RW   -> GND
 *   LCD E    -> GPIO 23
 *   LCD D4   -> GPIO 18
 *   LCD D5   -> GPIO 5
 *   LCD D6   -> GPIO 17
 *   LCD D7   -> GPIO 16
 *   LCD A    -> 5V (through 220 ohm if no built-in resistor)
 *   LCD K    -> GND
 *
 *   Signal pot: middle pin -> GPIO 34, outer pins -> 3.3V and GND
 *
 * Required library: LiquidCrystal (built into Arduino IDE -- no install needed).
 */

#include <LiquidCrystal.h>

#define POT_PIN          34
#define LOAD_STRENGTH    5000   // iterations of fake work per loop -- raise to make it worse
#define SAMPLE_PRINT_MS  500    // how often to print sample rate to Serial

// LCD pin assignments (4-bit parallel HD44780)
#define LCD_RS  19
#define LCD_EN  23
#define LCD_D4  18
#define LCD_D5  5
#define LCD_D6  17
#define LCD_D7  16

LiquidCrystal lcd(LCD_RS, LCD_EN, LCD_D4, LCD_D5, LCD_D6, LCD_D7);

// -- CPU load task ------------------------------------------------------------
// Simulates a busy processing task hogging the CPU
volatile float g_load_result = 0;

void runCpuLoad() {
  float x = 1.0;
  for (int i = 0; i < LOAD_STRENGTH; i++) {
    x = x * 1.0001f + 0.0001f;  // busy math the compiler won't optimize away
  }
  g_load_result = x;
}

// -- Sampling rate tracker ----------------------------------------------------
unsigned long g_sampleCount = 0;
unsigned long g_lastPrintMs = 0;

void setup() {
  Serial.begin(115200);

  lcd.begin(16, 2);

  lcd.setCursor(0, 0);
  lcd.print("CECS 460 Step 2");
  lcd.setCursor(0, 1);
  lcd.print("SW: Under Press.");
  delay(2000);
  lcd.clear();

  Serial.println("=== Step 2: Software Under Pressure ===");
  Serial.println("Turn the potentiometer and watch the LCD lag.");
  Serial.println("Sample rate printed every 500ms.");
}

void loop() {
  // -- CPU load -- runs every loop iteration, starving the ADC read ----------
  runCpuLoad();

  // -- Software ADC read ----------------------------------------------------
  int raw = analogRead(POT_PIN);          // 0-4095
  int percent = map(raw, 0, 4095, 0, 100);
  g_sampleCount++;

  // -- Update LCD -----------------------------------------------------------
  lcd.setCursor(0, 0);
  lcd.print("Knob:           ");
  lcd.setCursor(6, 0);
  lcd.print(percent);
  lcd.print("%   ");

  lcd.setCursor(0, 1);
  lcd.print("SW Poll  LAGGING");

  // -- Print sample rate to Serial ------------------------------------------
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
