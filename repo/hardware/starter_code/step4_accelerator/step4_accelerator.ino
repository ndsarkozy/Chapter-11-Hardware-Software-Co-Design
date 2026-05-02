/*
 * Step 4 — The Accelerator
 * CECS 460 Chapter 11: Hardware/Software Co-Design
 *
 * ╔══════════════════════════════════════════════════════════╗
 * ║  YOUR TASK: Change USE_DMA from 0 to 1 on line below.  ║
 * ║  Compile, flash, and observe the difference.            ║
 * ╚══════════════════════════════════════════════════════════╝
 *
 * USE_DMA = 0 → software analogRead() loop (same as Step 2 — slow)
 * USE_DMA = 1 → DMA controller fills ADC buffer at 10 kHz (fast)
 *
 * When USE_DMA=1 and your DMA sample rate holds above 200 Hz
 * for 5 seconds, the ESP32 connects to the classroom server
 * and reports your lab pass automatically.
 *
 * Hardware (identical to Steps 2–3):
 *   LCD I2C:       SDA → GPIO 21, SCL → GPIO 22, VCC → 5V, GND → GND
 *   Potentiometer: middle pin → GPIO 34, outer pins → 3.3V and GND
 *
 * Required libraries (Arduino IDE Library Manager):
 *   LiquidCrystal I2C  — by Frank de Brabander
 *   PubSubClient        — by Nick O'Leary
 *   ArduinoJson         — by Benoit Blanchon (v6.x)
 */

// ── STUDENT TASK ─────────────────────────────────────────────────────────────
#define USE_DMA  0   // ← CHANGE THIS TO 1 TO ENABLE DMA ACCELERATION
// ─────────────────────────────────────────────────────────────────────────────

// ── Network / server configuration ───────────────────────────────────────────
#define WIFI_SSID     "DEEZ"
#define WIFI_PASS     "password"
#define MQTT_HOST     "192.168.8.228"
#define MQTT_PORT     1883
#define COURSE        "C460"
#define LESSON_ID     "c460_ch11_codesign"
#define LAB_CHAPTER   "ch11Lab"
#define PASS_Q_ID     "q4_lab_pass"

// ── Hardware / timing config ──────────────────────────────────────────────────
#define POT_PIN         34
#define LOAD_STRENGTH   5000    // identical CPU load to Step 2
#define DMA_BUF_COUNT   4
#define DMA_BUF_LEN     256
#define DMA_SAMPLE_RATE 10000   // Hz — 10 kHz ADC via DMA
#define SAMPLE_PRINT_MS 500     // how often to print Hz to Serial
#define PASS_RATE_HZ    200.0f  // sustained rate above this triggers pass
#define PASS_SUSTAIN_MS 5000    // must hold above threshold for this long

// ─────────────────────────────────────────────────────────────────────────────

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <esp_wifi.h>

#if USE_DMA
#include <driver/i2s.h>
#include <driver/adc.h>
#endif

LiquidCrystal_I2C lcd(0x27, 16, 2);

WiFiClient   wifiClient;
PubSubClient mqtt(wifiClient);

// ── State ─────────────────────────────────────────────────────────────────────
static int            g_slot        = -1;
static String         g_token       = "";
static String         g_mac         = "";
static bool           g_passSent    = false;
static unsigned long  g_passStartMs = 0;  // when rate first crossed threshold

// ── Sampling rate tracker ─────────────────────────────────────────────────────
static unsigned long  g_sampleCount = 0;
static unsigned long  g_lastPrintMs = 0;
static float          g_lastRate    = 0;

// ── CPU load (identical to Step 2) ───────────────────────────────────────────
volatile float g_load_result = 0;
void runCpuLoad() {
  float x = 1.0;
  for (int i = 0; i < LOAD_STRENGTH; i++) {
    x = x * 1.0001f + 0.0001f;
  }
  g_load_result = x;
}

// ── DMA ADC (only compiled when USE_DMA=1) ───────────────────────────────────
#if USE_DMA
void setupDmaAdc() {
  i2s_config_t cfg = {
    .mode                 = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX | I2S_MODE_ADC_BUILT_IN),
    .sample_rate          = DMA_SAMPLE_RATE,
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
  i2s_driver_install(I2S_NUM_0, &cfg, 0, NULL);
  i2s_set_adc_mode(ADC_UNIT_1, ADC1_CHANNEL_6);  // GPIO 34
  i2s_adc_enable(I2S_NUM_0);
}

int readDmaAdc() {
  uint16_t buf[DMA_BUF_LEN];
  size_t bytesRead = 0;
  i2s_read(I2S_NUM_0, &buf, sizeof(buf), &bytesRead, 10 / portTICK_PERIOD_MS);
  int n = bytesRead / sizeof(uint16_t);
  if (n == 0) return -1;
  long sum = 0;
  for (int i = 0; i < n; i++) sum += (buf[i] & 0x0FFF);
  return sum / n;
}
#endif

// ── MAC address helper ────────────────────────────────────────────────────────
String getMac() {
  uint8_t m[6];
  esp_read_mac(m, ESP_MAC_WIFI_STA);
  char buf[13];
  snprintf(buf, sizeof(buf), "%02X%02X%02X%02X%02X%02X",
           m[0], m[1], m[2], m[3], m[4], m[5]);
  return String(buf);
}

// ── MQTT callback (receives slot + token assignment) ─────────────────────────
void mqttCallback(char* topic, byte* payload, unsigned int len) {
  String t(topic);
  StaticJsonDocument<256> doc;
  if (deserializeJson(doc, payload, len) != DeserializationError::Ok) return;

  String assignTopic = String(COURSE) + "/device/assign/" + g_mac;
  if (t == assignTopic) {
    g_slot  = doc["slot"] | -1;
    g_token = doc["token"] | "";
    Serial.print("[MQTT] Assigned slot="); Serial.print(g_slot);
    Serial.print(" token="); Serial.println(g_token);
  }
}

// ── WiFi + MQTT maintenance (call from loop) ──────────────────────────────────
static unsigned long g_wifiRetry = 0;
static unsigned long g_mqttRetry = 0;
static bool          g_announced = false;

void maintainNetwork() {
  // WiFi
  if (WiFi.status() != WL_CONNECTED) {
    g_announced = false;
    if (millis() - g_wifiRetry > 8000) {
      g_wifiRetry = millis();
      WiFi.mode(WIFI_STA);
      WiFi.begin(WIFI_SSID, WIFI_PASS);
    }
    return;
  }

  // MQTT connect
  if (!mqtt.connected()) {
    g_announced = false;
    if (millis() - g_mqttRetry > 5000) {
      g_mqttRetry = millis();
      String cid = "cecs460_step4_" + g_mac;
      if (mqtt.connect(cid.c_str())) {
        mqtt.subscribe((String(COURSE) + "/device/assign/" + g_mac).c_str());
        Serial.println("[MQTT] Connected to server");
      }
    }
    return;
  }

  mqtt.loop();

  // Announce once after connect
  if (!g_announced) {
    g_announced = true;
    StaticJsonDocument<128> doc;
    doc["mac"]       = g_mac;
    doc["device_id"] = "esp32_" + g_mac.substring(6);
    doc["firmware"]  = "step4_v1";
    String out;
    serializeJson(doc, out);
    mqtt.publish((String(COURSE) + "/device/announce").c_str(), out.c_str());
    Serial.println("[MQTT] Announced — waiting for slot assignment");
  }
}

// ── Publish lab pass ──────────────────────────────────────────────────────────
void publishPass(float rate) {
  if (!mqtt.connected() || g_slot < 0 || g_passSent) return;

  StaticJsonDocument<128> doc;
  doc["slot"]    = g_slot;
  doc["token"]   = g_token;
  doc["chapter"] = LAB_CHAPTER;
  JsonObject ans = doc.createNestedObject("answers");
  ans[PASS_Q_ID] = "PASS";
  String out;
  serializeJson(doc, out);

  String topic = String(LESSON_ID) + "/" + String(g_slot) + "/answer";
  mqtt.publish(topic.c_str(), out.c_str());
  g_passSent = true;

  Serial.print("[MQTT] Lab PASS sent! DMA rate was ");
  Serial.print(rate, 1);
  Serial.println(" Hz");
  lcd.setCursor(0, 1);
  lcd.print("DMA PASS SENT!  ");
}

// ─────────────────────────────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);

  Wire.begin(21, 22);
  lcd.init();
  lcd.backlight();

#if USE_DMA
  lcd.setCursor(0, 0); lcd.print("Step4: DMA Mode ");
  lcd.setCursor(0, 1); lcd.print("Setting up DMA..");
  delay(500);
  setupDmaAdc();
  Serial.println("=== Step 4: DMA Accelerator (USE_DMA=1) ===");
  Serial.println("DMA handles ADC at 10 kHz. CPU load no longer starves the ADC.");
#else
  lcd.setCursor(0, 0); lcd.print("Step4: SW Mode  ");
  lcd.setCursor(0, 1); lcd.print("USE_DMA is 0!   ");
  delay(500);
  Serial.println("=== Step 4: Software Mode (USE_DMA=0) ===");
  Serial.println("Still using analogRead() — same lag as Step 2.");
  Serial.println("Change USE_DMA to 1 and reflash to enable DMA.");
#endif

  lcd.clear();

  g_mac = getMac();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(mqttCallback);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.println("[WiFi] Connecting to " + String(WIFI_SSID) + "...");
}

void loop() {
  // ── Network maintenance ───────────────────────────────────────────────────
  maintainNetwork();

  // ── CPU load (same as Step 2) ─────────────────────────────────────────────
  runCpuLoad();

  // ── ADC read ──────────────────────────────────────────────────────────────
  int raw = -1;
#if USE_DMA
  raw = readDmaAdc();
  if (raw < 0) return;
#else
  raw = analogRead(POT_PIN);
#endif

  int percent = map(raw, 0, 4095, 0, 100);
  g_sampleCount++;

  // ── LCD update ────────────────────────────────────────────────────────────
  if (!g_passSent) {
    lcd.setCursor(0, 0);
    lcd.print("Knob:           ");
    lcd.setCursor(6, 0);
    lcd.print(percent);
    lcd.print("%   ");

    lcd.setCursor(0, 1);
#if USE_DMA
    lcd.print("DMA      SMOOTH ");
#else
    lcd.print("SW Poll  LAGGING");
#endif
  }

  // ── Sample rate print + pass check ───────────────────────────────────────
  unsigned long now = millis();
  if (now - g_lastPrintMs >= SAMPLE_PRINT_MS) {
    unsigned long elapsed = now - g_lastPrintMs;
    float rate = (float)g_sampleCount / (elapsed / 1000.0f);
    g_lastRate = rate;
    g_sampleCount = 0;
    g_lastPrintMs = now;

#if USE_DMA
    Serial.print("[DMA] Sample rate: ");
#else
    Serial.print("[SW]  Sample rate: ");
#endif
    Serial.print(rate, 1);
    Serial.print(" Hz  |  Knob: ");
    Serial.print(percent);
    Serial.print("%");

#if USE_DMA
    if (rate >= PASS_RATE_HZ) {
      if (g_passStartMs == 0) g_passStartMs = now;
      unsigned long sustained = now - g_passStartMs;
      Serial.print("  [pass check: ");
      Serial.print(sustained / 1000);
      Serial.print("s/");
      Serial.print(PASS_SUSTAIN_MS / 1000);
      Serial.print("s]");
      if (sustained >= PASS_SUSTAIN_MS && !g_passSent) {
        publishPass(rate);
      }
    } else {
      g_passStartMs = 0;  // reset sustain timer if rate drops
    }
#else
    if (!g_passSent) {
      Serial.print("  [USE_DMA=0 — change to 1 to enable pass]");
    }
#endif
    Serial.println();
  }
}
