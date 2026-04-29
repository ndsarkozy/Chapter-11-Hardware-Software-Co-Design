/*
 * Step 4 — The Accelerator
 * CECS 460 Chapter 11: Hardware/Software Co-Design
 *
 * Same hardware and same CPU load as Step 2 — but ADC sampling
 * is now handled by the ESP32's DMA controller via the I2S peripheral
 * in ADC mode. The CPU no longer polls the ADC; it just reads a
 * buffer that DMA filled automatically.
 *
 * Expected result: LCD updates remain fast and smooth even under
 * the same CPU load that made Step 2 lag.
 *
 * Hardware (identical to Step 2):
 *   LCD I2C: SDA → GPIO 21, SCL → GPIO 22, VCC → 5V, GND → GND
 *   Potentiometer: middle pin → GPIO 34, outer pins → 3.3V and GND
 */

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <driver/i2s.h>
#include <driver/adc.h>

#define POT_PIN         ADC1_CHANNEL_6   // GPIO 34 = ADC1 channel 6
#define LOAD_STRENGTH   5000             // same load as Step 2
#define DMA_BUF_COUNT   4
#define DMA_BUF_LEN     256
#define SAMPLE_PRINT_MS 500

LiquidCrystal_I2C lcd(0x27, 16, 2);

// ── CPU load task (identical to Step 2) ─────────────────────────────────────
volatile float g_load_result = 0;

void runCpuLoad() {
  float x = 1.0;
  for (int i = 0; i < LOAD_STRENGTH; i++) {
    x = x * 1.0001f + 0.0001f;
  }
  g_load_result = x;
}

// ── DMA ADC setup via I2S ────────────────────────────────────────────────────
void setupDmaAdc() {
  i2s_config_t i2s_config = {
    .mode                 = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX | I2S_MODE_ADC_BUILT_IN),
    .sample_rate          = 10000,       // 10 kHz sample rate
    .bits_per_sample      = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format       = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags     = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count        = DMA_BUF_COUNT,
    .dma_buf_len          = DMA_BUF_LEN,
    .use_apll             = false,
    .tx_desc_auto_clear   = false,
    .fixed_mclk           = 0
  };

  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_adc_mode(ADC_UNIT_1, POT_PIN);
  i2s_adc_enable(I2S_NUM_0);
}

// ── Read latest ADC value from DMA buffer ────────────────────────────────────
int readDmaAdc() {
  uint16_t buf[DMA_BUF_LEN];
  size_t bytesRead = 0;
  i2s_read(I2S_NUM_0, &buf, sizeof(buf), &bytesRead, 10 / portTICK_PERIOD_MS);

  int samples = bytesRead / sizeof(uint16_t);
  if (samples == 0) return -1;

  // Average the buffer for a stable reading
  long sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += (buf[i] & 0x0FFF);  // ESP32 I2S ADC packs 12-bit value in lower bits
  }
  return sum / samples;
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
  lcd.print("CECS 460 Step 4");
  lcd.setCursor(0, 1);
  lcd.print("DMA Accelerator");
  delay(2000);
  lcd.clear();

  setupDmaAdc();

  Serial.println("=== Step 4: The Accelerator ===");
  Serial.println("DMA handles ADC sampling. CPU load no longer affects the knob.");
  Serial.println("Sample rate printed every 500ms.");
}

void loop() {
  // ── Same CPU load as Step 2 ──────────────────────────────────────────────
  runCpuLoad();

  // ── DMA ADC read — CPU just picks up what DMA already collected ──────────
  int raw = readDmaAdc();
  if (raw < 0) return;

  int percent = map(raw, 0, 4095, 0, 100);
  g_sampleCount++;

  // ── Update LCD ───────────────────────────────────────────────────────────
  lcd.setCursor(0, 0);
  lcd.print("Knob:           ");
  lcd.setCursor(6, 0);
  lcd.print(percent);
  lcd.print("%   ");

  lcd.setCursor(0, 1);
  lcd.print("DMA      SMOOTH ");

  // ── Print sample rate to Serial ──────────────────────────────────────────
  unsigned long now = millis();
  if (now - g_lastPrintMs >= SAMPLE_PRINT_MS) {
    unsigned long elapsed = now - g_lastPrintMs;
    float rate = (float)g_sampleCount / (elapsed / 1000.0f);
    Serial.print("[DMA] Sample rate: ");
    Serial.print(rate, 1);
    Serial.print(" Hz  |  Knob: ");
    Serial.print(percent);
    Serial.println("%");
    g_sampleCount = 0;
    g_lastPrintMs = now;
  }
}
