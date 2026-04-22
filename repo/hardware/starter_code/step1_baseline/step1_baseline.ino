/*
 * CECS 460 Chapter 11 — Step 1: Baseline Blink
 *
 * Goal: Blink an LED on GPIO 18 at exactly 1 Hz (50% duty cycle)
 *       using the simplest software approach possible.
 *
 * Hardware:
 *   - LED anode  -> GPIO 18 (through 330 Ω current-limiting resistor)
 *   - LED cathode -> GND
 *   - Scope probe on GPIO 18, ground clip on GND
 *
 * Your task:
 *   1. Flash this sketch to the ESP32.
 *   2. Measure the actual frequency on the scope.
 *   3. Record it in your lab notebook.
 *   4. Answer the Step 1 question in the lesson.
 *
 * Nothing is wrong with this code. It just isn't perfect. Why?
 */

const int LED_PIN = 18;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(115200);
  Serial.println("Step 1: Baseline 1 Hz blink running");
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  delay(500);                    // 500 ms on
  digitalWrite(LED_PIN, LOW);
  delay(500);                    // 500 ms off
}
