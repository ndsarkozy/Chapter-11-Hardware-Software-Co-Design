/*
 * CECS 460 Chapter 11 — Step 1: Baseline Blink
 *
 * Goal: Blink an LED on GPIO 18 at exactly 1 Hz (50% duty cycle)
 *       using the simplest software approach possible.
 *
 * Hardware:
 *   - LED anode  -> GPIO 18 (through 330 Ω current-limiting resistor)
 *   - LED cathode -> GND
 *
 * Your task:
 *   1. Flash this sketch to the ESP32.
 *   2. Open Serial Monitor at 115200 baud.
 *   3. Read the measured period and frequency printed each cycle.
 *   4. Record the frequency in the lesson.
 *
 * Nothing is wrong with this code. It just isn't perfect. Why?
 */

const int LED_PIN = 18;

unsigned long g_cycleStart = 0;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(115200);
  Serial.println("Step 1: Baseline 1 Hz blink — open Serial Monitor at 115200 baud");
  Serial.println("Period (ms) and frequency (Hz) printed each full cycle.");
  g_cycleStart = millis();
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  delay(500);                    // 500 ms on
  digitalWrite(LED_PIN, LOW);
  delay(500);                    // 500 ms off

  // Measure the actual elapsed time for this full cycle
  unsigned long now = millis();
  unsigned long period_ms = now - g_cycleStart;
  g_cycleStart = now;

  float freq_hz = 1000.0f / (float)period_ms;
  Serial.print("Period: ");
  Serial.print(period_ms);
  Serial.print(" ms  |  Frequency: ");
  Serial.print(freq_hz, 4);
  Serial.println(" Hz");
}
