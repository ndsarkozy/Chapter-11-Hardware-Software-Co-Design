// 04_visual_demo.ino
// CECS 460 — Chapter 11: Hardware/Software Co-Design
// Three LEDs, one frequency — software vs. ISR vs. LEDC peripheral
//
// Wiring:
//   LED1 — GPIO 18 — 220Ω resistor — GND  (software delayMicroseconds)
//   LED2 — GPIO 19 — 220Ω resistor — GND  (hardware timer ISR)
//   LED3 — GPIO 21 — 220Ω resistor — GND  (LEDC peripheral, zero CPU after setup)
//
// Targets Arduino-ESP32 core 3.x on DOIT DevKit V1
// Serial: 115200 baud
// Commands: l=cycle load, +=double freq, -=halve freq, r=reset

#include <Arduino.h>

// ---------- pin assignments ----------
#define PIN_SW    18   // LED1: software busy-wait
#define PIN_ISR   19   // LED2: hardware timer ISR
#define PIN_LEDC  21   // LED3: LEDC peripheral

// ---------- frequency / timing ----------
static float  targetHz   = 5.0f;
static uint32_t halfPeriodUs = 0;   // half-period in µs, recomputed on freq change

// ---------- load levels ----------
enum LoadLevel { LOAD_NONE = 0, LOAD_LIGHT, LOAD_HEAVY, LOAD_BRUTAL, LOAD_COUNT };
static const char* LOAD_NAMES[] = { "NONE", "LIGHT", "HEAVY", "BRUTAL" };
static LoadLevel currentLoad = LOAD_NONE;

// ---------- measurement (LED1 SW) ----------
static volatile uint32_t sw_toggleCount  = 0;
static uint32_t sw_lastMeasureUs  = 0;
static float    sw_measuredHz     = 0.0f;

// ---------- measurement (LED2 ISR) ----------
static volatile uint32_t isr_toggleCount = 0;
static uint32_t isr_lastMeasureUs = 0;
static float    isr_measuredHz    = 0.0f;

// ---------- timer handle (core 3.x) ----------
static hw_timer_t* timerHandle = NULL;

// ---------- ISR ----------
void IRAM_ATTR onTimerISR() {
  digitalWrite(PIN_ISR, !digitalRead(PIN_ISR));
  isr_toggleCount++;
}

// ---------- helpers ----------
static void recomputeHalfPeriod() {
  if (targetHz <= 0.0f) targetHz = 1.0f;
  halfPeriodUs = (uint32_t)(500000.0f / targetHz);   // half-period in µs
}

static void applyTimerFreq() {
  // Restart timer with new half-period.
  // core 3.x API: timerBegin(freq_hz) — the timer increments at freq_hz ticks/sec.
  // We want an interrupt every halfPeriodUs microseconds.
  // Use 1 MHz tick rate → alarm = halfPeriodUs ticks.
  if (timerHandle) {
    timerEnd(timerHandle);
  }
  timerHandle = timerBegin(1000000);          // 1 MHz tick rate
  timerAttachInterrupt(timerHandle, &onTimerISR);
  timerAlarm(timerHandle, halfPeriodUs, true, 0);
}

static void applyLEDCFreq() {
  // 50% duty cycle, 10-bit resolution → duty = 512
  ledcDetach(PIN_LEDC);
  ledcAttach(PIN_LEDC, (uint32_t)targetHz, 10);
  ledcWrite(PIN_LEDC, 512);
}

static void applyFrequency() {
  recomputeHalfPeriod();
  applyTimerFreq();
  applyLEDCFreq();
  // Reset measurement counters
  sw_toggleCount        = 0;
  sw_lastMeasureUs      = micros();
  isr_toggleCount       = 0;
  isr_lastMeasureUs     = micros();
  sw_measuredHz         = 0.0f;
  isr_measuredHz        = 0.0f;
}

// ---------- load task ----------
static void runLoad(LoadLevel level) {
  switch (level) {
    case LOAD_NONE:
      break;
    case LOAD_LIGHT:
      { volatile uint32_t x = 0;
        for (uint32_t i = 0; i < 50000UL; i++) x += i * 3;
        (void)x;
      }
      break;
    case LOAD_HEAVY:
      { volatile uint32_t x = 0;
        for (uint32_t i = 0; i < 500000UL; i++) x += i * 3;
        (void)x;
      }
      break;
    case LOAD_BRUTAL:
      { volatile uint32_t x = 0;
        for (uint32_t i = 0; i < 5000000UL; i++) x += i * 3;
        (void)x;
      }
      break;
    default:
      break;
  }
}

// ---------- setup ----------
void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);

  pinMode(PIN_SW,  OUTPUT);
  pinMode(PIN_ISR, OUTPUT);

  digitalWrite(PIN_SW,  LOW);
  digitalWrite(PIN_ISR, LOW);

  recomputeHalfPeriod();
  applyFrequency();

  Serial.println(F("04_visual_demo ready. Commands: l=cycle load, +=double freq, -=halve, r=reset"));
}

// ---------- loop ----------
void loop() {
  // --- serial commands ---
  if (Serial.available()) {
    char c = (char)Serial.read();
    if (c == 'l') {
      currentLoad = (LoadLevel)((currentLoad + 1) % LOAD_COUNT);
      Serial.print(F("Load -> "));
      Serial.println(LOAD_NAMES[currentLoad]);
    } else if (c == '+') {
      targetHz *= 2.0f;
      if (targetHz > 100000.0f) targetHz = 100000.0f;
      applyFrequency();
      Serial.print(F("Freq -> "));
      Serial.print(targetHz);
      Serial.println(F(" Hz"));
    } else if (c == '-') {
      targetHz /= 2.0f;
      if (targetHz < 0.1f) targetHz = 0.1f;
      applyFrequency();
      Serial.print(F("Freq -> "));
      Serial.print(targetHz);
      Serial.println(F(" Hz"));
    } else if (c == 'r') {
      targetHz   = 5.0f;
      currentLoad = LOAD_NONE;
      applyFrequency();
      Serial.println(F("Reset -> 5 Hz, LOAD=NONE"));
    }
  }

  // --- software LED1: busy-wait toggle ---
  uint32_t t0 = micros();
  digitalWrite(PIN_SW, HIGH);
  sw_toggleCount++;
  runLoad(currentLoad);                    // load runs during the HIGH half
  uint32_t elapsed = micros() - t0;
  uint32_t remaining = (elapsed < halfPeriodUs) ? (halfPeriodUs - elapsed) : 0;
  if (remaining > 0) delayMicroseconds(remaining);

  t0 = micros();
  digitalWrite(PIN_SW, LOW);
  sw_toggleCount++;
  runLoad(currentLoad);                    // load runs during the LOW half too
  elapsed = micros() - t0;
  remaining = (elapsed < halfPeriodUs) ? (halfPeriodUs - elapsed) : 0;
  if (remaining > 0) delayMicroseconds(remaining);

  // --- 1-second reporting window ---
  uint32_t nowUs = micros();

  // LED1 measurement
  uint32_t sw_dt = nowUs - sw_lastMeasureUs;
  if (sw_dt >= 1000000UL) {
    uint32_t cnt = sw_toggleCount;
    sw_toggleCount = 0;
    sw_lastMeasureUs = nowUs;
    // Each full cycle = 2 toggles
    sw_measuredHz = (cnt / 2.0f) / (sw_dt / 1e6f);
  }

  // LED2 measurement
  uint32_t isr_dt = nowUs - isr_lastMeasureUs;
  if (isr_dt >= 1000000UL) {
    uint32_t cnt = isr_toggleCount;
    isr_toggleCount = 0;
    isr_lastMeasureUs = nowUs;
    isr_measuredHz = (cnt / 2.0f) / (isr_dt / 1e6f);
  }

  // Print once per ~second (tied to SW loop cadence — approximately every 2*halfPeriod)
  static uint32_t lastPrintUs = 0;
  if ((nowUs - lastPrintUs) >= 1000000UL) {
    lastPrintUs = nowUs;

    float sw_err  = (targetHz > 0) ? ((sw_measuredHz  - targetHz) / targetHz * 100.0f) : 0.0f;
    float isr_err = (targetHz > 0) ? ((isr_measuredHz - targetHz) / targetHz * 100.0f) : 0.0f;

    char buf[120];
    snprintf(buf, sizeof(buf),
      "LED1(SW)=%.2f Hz [%.1f%%]   LED2(ISR)=%.2f Hz [%.1f%%]   LED3(LEDC)=locked   LOAD=%s",
      sw_measuredHz,  sw_err,
      isr_measuredHz, isr_err,
      LOAD_NAMES[currentLoad]);
    Serial.println(buf);
  }
}
