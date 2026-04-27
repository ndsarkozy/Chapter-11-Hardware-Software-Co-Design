/*
 * CECS460_Lab11_AES.ino
 * =====================
 * ESP32 classroom firmware for CECS 460
 * Chapter 11 — Hardware/Software Co-Design
 * Hardware: ESP32 DevKit-C (Xtensa LX6), no external components required
 *
 * Features:
 *  - Wi-Fi + MQTT with MAC-based slot/token assignment (matches all other labs)
 *  - Software AES-128 ECB (self-contained, no hardware acceleration)
 *  - Hardware AES-128 ECB via ESP-IDF esp_aes driver
 *  - Benchmark: 1000 iterations each, avg µs/block measured with esp_timer
 *  - Auto-submits structured telemetry: [hw:sw_us=X hw_us=Y speedup=Z blocks=1000]
 *  - Continuous bench telemetry published every BENCH_PUBLISH_MS
 *  - Serial reflection answer submission for q_lab2
 *  - Full serial command interface (matches ch9 pattern)
 *
 * Version: 1.0.0
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include <esp_system.h>
#include <esp_timer.h>
#include "mbedtls/aes.h"   // Arduino-ESP32 3.x compatible

// AES round key type — must be declared before function definitions
typedef uint8_t AesRoundKey[176];  // 11 round keys x 16 bytes

#define FW_VERSION        "1.0.0"
#define FW_DATE           "2026-04"

// ── Default config ──────────────────────────────────────────────────────────
#define DEFAULT_SSID      "CECS"
#define DEFAULT_PASS      "CECS-Classroom"
#define DEFAULT_MQTT_HOST "192.168.8.10"
#define DEFAULT_MQTT_PORT 1883
#define HEARTBEAT_MS      10000UL
#define BENCH_PUBLISH_MS  10000UL
#define LED_PIN           2           // Built-in LED on most ESP32 DevKit-C boards

// ── MQTT topics ─────────────────────────────────────────────────────────────
#define COURSE  "C460"
#define LESSON  "c460_ch11_codesign"

// ── NVS namespace ───────────────────────────────────────────────────────────
#define NVS_NS  "cecs460"

// ── Benchmark config ────────────────────────────────────────────────────────
#define BENCH_ITERATIONS  1000
#define BENCH_WARMUP       10

// AES-128 test vector (FIPS 197 Appendix B)
static const uint8_t TEST_KEY[16] = {
  0x2b,0x7e,0x15,0x16, 0x28,0xae,0xd2,0xa6,
  0xab,0xf7,0x15,0x88, 0x09,0xcf,0x4f,0x3c
};
static const uint8_t TEST_PLAIN[16] = {
  0x32,0x43,0xf6,0xa8, 0x88,0x5a,0x30,0x8d,
  0x31,0x31,0x98,0xa2, 0xe0,0x37,0x07,0x34
};
// Expected ciphertext: 39 25 84 1d 02 dc 09 fb dc 11 85 97 19 6a 0b 32

// ── Globals ─────────────────────────────────────────────────────────────────
Preferences  prefs;
WiFiClient   wifiClient;
PubSubClient mqtt(wifiClient);

String  g_ssid, g_pass, g_mqttHost;
int     g_mqttPort;
String  g_deviceId, g_mac, g_studentId;
int     g_slot    = -1;
String  g_token   = "";
bool    g_verbose = false;
bool    g_announced = false;

unsigned long g_wifiRetry   = 0;
unsigned long g_mqttRetry   = 0;
unsigned long g_lastHB      = 0;
unsigned long g_lastBenchPub= 0;
int           g_mqttBackoff = 2000;
int           g_dotCount    = 0;
bool          g_prevSameLine= false;

// Benchmark results
long    g_sw_us      = 0;   // avg µs per block, SW path
long    g_hw_us      = 0;   // avg µs per block, HW path
float   g_speedup    = 0.0f;
bool    g_benchDone  = false;
bool    g_labAnswered= false;
bool    g_hwAnswerOk = false;  // set true when hw result auto-submitted

// ── Serial helpers ───────────────────────────────────────────────────────────
void serialLine(const String& s) {
  if (g_prevSameLine) { Serial.println(); g_dotCount = 0; g_prevSameLine = false; }
  Serial.println(s);
}
void serialDot() {
  Serial.print("."); g_dotCount++;
  g_prevSameLine = true;
  if (g_dotCount >= 60) { Serial.println(); g_dotCount = 0; g_prevSameLine = false; }
}
void verboseLog(const String& s) { if (g_verbose) serialLine("[DBG] " + s); }

// ── NVS ─────────────────────────────────────────────────────────────────────
void loadPrefs() {
  prefs.begin(NVS_NS, true);
  g_ssid      = prefs.getString("ssid",     DEFAULT_SSID);
  g_pass      = prefs.getString("pass",     DEFAULT_PASS);
  g_mqttHost  = prefs.getString("mqttHost", DEFAULT_MQTT_HOST);
  g_mqttPort  = prefs.getInt   ("mqttPort", DEFAULT_MQTT_PORT);
  g_studentId = prefs.getString("student",  "");
  g_slot      = prefs.getInt   ("slot",     -1);
  g_token     = prefs.getString("token",    "");
  g_verbose   = prefs.getBool  ("verbose",  false);
  g_deviceId  = prefs.getString("deviceId", "");
  prefs.end();
}
void savePref   (const String& k, const String& v) { prefs.begin(NVS_NS,false); prefs.putString(k.c_str(),v.c_str()); prefs.end(); }
void savePrefInt(const String& k, int v)            { prefs.begin(NVS_NS,false); prefs.putInt(k.c_str(),v);            prefs.end(); }
void savePrefBool(const String& k, bool v)          { prefs.begin(NVS_NS,false); prefs.putBool(k.c_str(),v);           prefs.end(); }
void clearAssignment() {
  prefs.begin(NVS_NS,false); prefs.remove("slot"); prefs.remove("token"); prefs.end();
  g_slot = -1; g_token = ""; g_announced = false; g_labAnswered = false; g_hwAnswerOk = false;
  serialLine("[NVS] Assignment cleared — will re-announce");
}

// ── MAC ──────────────────────────────────────────────────────────────────────
String getMac() {
  String mac = WiFi.macAddress();  // "AA:BB:CC:DD:EE:FF"
  mac.replace(":", "");
  mac.toUpperCase();
  return mac;
}

// ── Wi-Fi ────────────────────────────────────────────────────────────────────
void checkWifi() {
  static bool prev = false;
  bool conn = (WiFi.status() == WL_CONNECTED);
  if (conn && !prev) {
    serialLine("[WiFi] Connected! IP:" + WiFi.localIP().toString() + " RSSI:" + String(WiFi.RSSI()) + "dBm");
    g_mqttBackoff = 2000; g_announced = false;
  } else if (!conn && prev) {
    serialLine("[WiFi] Disconnected");
  }
  prev = conn;
  if (!conn) {
    unsigned long now = millis();
    if (now - g_wifiRetry >= 8000) {
      g_wifiRetry = now;
      serialLine("[WiFi] Connecting to " + g_ssid + "...");
      WiFi.mode(WIFI_STA);
      WiFi.begin(g_ssid.c_str(), g_pass.c_str());
    }
  }
}

// ── MQTT callback ─────────────────────────────────────────────────────────────
void mqttCallback(char* topic, byte* payload, unsigned int len) {
  String t(topic), p;
  for (unsigned int i = 0; i < len; i++) p += (char)payload[i];
  verboseLog("MQTT RX " + t + " : " + p);

  // Slot assignment
  if (t == String(COURSE) + "/device/assign/" + g_mac) {
    JsonDocument doc;
    if (deserializeJson(doc, p) == DeserializationError::Ok) {
      g_slot  = doc["slot"].as<int>();
      g_token = doc["token"].as<String>();
      String url = doc["student_url"].as<String>();
      savePrefInt("slot", g_slot); savePref("token", g_token);
      serialLine("");
      serialLine("╔══════════════════════════════════════════════════════╗");
      serialLine("║              SLOT ASSIGNED                           ║");
      serialLine("╠══════════════════════════════════════════════════════╣");
      serialLine("║ Slot   : " + String(g_slot));
      serialLine("║ Token  : " + g_token);
      serialLine("║ URL    : " + url);
      serialLine("╚══════════════════════════════════════════════════════╝");
      // Re-submit benchmark result if already computed
      if (g_benchDone && !g_hwAnswerOk) {
        serialLine("[MQTT] Benchmark already complete — resubmitting result...");
      }
    }
  }
  // Lesson step broadcast
  if (t == String(LESSON) + "/control/step") {
    JsonDocument doc;
    if (deserializeJson(doc, p) == DeserializationError::Ok)
      serialLine("[Lesson] Active step → " + String(doc["step"].as<int>()));
  }
  // Instructor broadcast
  if (t == String(LESSON) + "/control/broadcast") {
    JsonDocument doc;
    if (deserializeJson(doc, p) == DeserializationError::Ok)
      serialLine("[Broadcast] " + doc["message"].as<String>());
  }
}

// ── MQTT connect ──────────────────────────────────────────────────────────────
void checkMqtt() {
  if (WiFi.status() != WL_CONNECTED) return;
  if (mqtt.connected()) { g_mqttBackoff = 2000; return; }
  unsigned long now = millis();
  if (now - g_mqttRetry < (unsigned long)g_mqttBackoff) return;
  g_mqttRetry = now;
  serialLine("[MQTT] Connecting to " + g_mqttHost + ":" + String(g_mqttPort) + "...");
  String cid = g_deviceId + "_" + String(random(0xffff), HEX);
  if (mqtt.connect(cid.c_str())) {
    serialLine("[MQTT] Connected");
    g_mqttBackoff = 2000;
    mqtt.subscribe((String(COURSE) + "/device/assign/" + g_mac).c_str());
    mqtt.subscribe((String(LESSON) + "/control/step").c_str());
    mqtt.subscribe((String(LESSON) + "/control/broadcast").c_str());
    g_announced = false;
  } else {
    serialLine("[MQTT] Failed rc=" + String(mqtt.state()) + ", retry in " + String(g_mqttBackoff/1000) + "s");
    g_mqttBackoff = min(g_mqttBackoff * 2, 30000);
  }
}

void announce() {
  if (!mqtt.connected()) return;
  JsonDocument doc;
  doc["mac"] = g_mac; doc["device_id"] = g_deviceId; doc["firmware"] = FW_VERSION;
  if (g_slot > 0) doc["saved_slot"] = g_slot;
  if (g_token.length()) doc["saved_token"] = g_token;
  if (g_studentId.length()) doc["student_id"] = g_studentId;
  String out; serializeJson(doc, out);
  mqtt.publish((String(COURSE) + "/device/announce").c_str(), out.c_str());
  serialLine("[MQTT] Announce sent (MAC=" + g_mac + ")");
  g_announced = true;
}

// ── MQTT publish helpers ──────────────────────────────────────────────────────
void publishBenchTelemetry() {
  if (!mqtt.connected() || g_slot < 0 || !g_benchDone) return;
  JsonDocument doc;
  doc["slot"]    = g_slot;
  doc["sw_us"]   = g_sw_us;
  doc["hw_us"]   = g_hw_us;
  doc["speedup"] = g_speedup;
  doc["blocks"]  = BENCH_ITERATIONS;
  doc["bench_done"] = g_benchDone;
  String out; serializeJson(doc, out);
  mqtt.publish((String(LESSON) + "/" + String(g_slot) + "/bench").c_str(), out.c_str());
  verboseLog("Bench telemetry: " + out);
}

void publishHwAnswer() {
  // Auto-submit the hw_result answer for q_lab1 in the format the grading engine expects
  if (!mqtt.connected() || g_slot < 0 || !g_benchDone) return;
  char buf[128];
  snprintf(buf, sizeof(buf),
           "[hw:sw_us=%ld hw_us=%ld speedup=%d blocks=%d]",
           g_sw_us, g_hw_us, (int)g_speedup, BENCH_ITERATIONS);
  JsonDocument doc;
  doc["slot"]    = g_slot;
  doc["token"]   = g_token;
  doc["step"]    = "q_lab1";
  doc["answer"]  = String(buf);
  String out; serializeJson(doc, out);
  mqtt.publish((String(LESSON) + "/" + String(g_slot) + "/answer").c_str(), out.c_str());
  serialLine("[MQTT] q_lab1 auto-submitted: " + String(buf));
  g_hwAnswerOk = true;
}

void publishReflectionAnswer(const String& text) {
  if (!mqtt.connected() || g_slot < 0) {
    serialLine("[MQTT] Not connected or no slot — answer not sent");
    return;
  }
  JsonDocument doc;
  doc["slot"]   = g_slot;
  doc["token"]  = g_token;
  doc["step"]   = "q_lab2";
  doc["answer"] = text;
  String out; serializeJson(doc, out);
  mqtt.publish((String(LESSON) + "/" + String(g_slot) + "/answer").c_str(), out.c_str());
  serialLine("[MQTT] q_lab2 submitted (" + String(text.length()) + " chars)");
  g_labAnswered = true;
}

void publishStatus() {
  if (!mqtt.connected() || g_slot < 0) return;
  JsonDocument doc;
  doc["slot"]      = g_slot;
  doc["ip"]        = WiFi.localIP().toString();
  doc["rssi"]      = WiFi.RSSI();
  doc["uptime"]    = millis() / 1000;
  doc["firmware"]  = FW_VERSION;
  doc["free_heap"] = ESP.getFreeHeap();
  doc["bench_done"]= g_benchDone;
  if (g_benchDone) { doc["sw_us"] = g_sw_us; doc["hw_us"] = g_hw_us; doc["speedup"] = g_speedup; }
  if (g_studentId.length()) doc["student_id"] = g_studentId;
  String out; serializeJson(doc, out);
  mqtt.publish((String(COURSE) + "/device/status/" + String(g_slot)).c_str(), out.c_str());
  if (g_verbose) serialLine("[HB] " + out); else serialDot();
}

// ═══════════════════════════════════════════════════════════════════════════
// SOFTWARE AES-128 (pure C, no hardware acceleration)
// Based on FIPS 197. Self-contained — no external headers required.
// ═══════════════════════════════════════════════════════════════════════════

static const uint8_t SW_SBOX[256] = {
  0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
  0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
  0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
  0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
  0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
  0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
  0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
  0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
  0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
  0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
  0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
  0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
  0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
  0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
  0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
  0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16
};
static const uint8_t SW_RCON[11] = {
  0x00,0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1b,0x36
};

static uint8_t sw_xtime(uint8_t x) {
  return (x << 1) ^ ((x & 0x80) ? 0x1b : 0x00);
}
static uint8_t sw_gmul(uint8_t a, uint8_t b) {
  uint8_t p = 0;
  for (int i = 0; i < 8; i++) {
    if (b & 1) p ^= a;
    bool hi = a & 0x80;
    a <<= 1;
    if (hi) a ^= 0x1b;
    b >>= 1;
  }
  return p;
}

static void swAesKeyExpansion(const uint8_t* key, AesRoundKey rk) {
  memcpy(rk, key, 16);
  for (int i = 4; i < 44; i++) {
    uint8_t temp[4];
    memcpy(temp, rk + (i-1)*4, 4);
    if (i % 4 == 0) {
      uint8_t t = temp[0];
      temp[0] = SW_SBOX[temp[1]] ^ SW_RCON[i/4];
      temp[1] = SW_SBOX[temp[2]];
      temp[2] = SW_SBOX[temp[3]];
      temp[3] = SW_SBOX[t];
    }
    for (int j = 0; j < 4; j++)
      rk[i*4+j] = rk[(i-4)*4+j] ^ temp[j];
  }
}

static void swAesEncryptBlock(const AesRoundKey rk, const uint8_t* in, uint8_t* out) {
  uint8_t state[16];
  // AddRoundKey (round 0)
  for (int i = 0; i < 16; i++) state[i] = in[i] ^ rk[i];

  for (int round = 1; round <= 10; round++) {
    // SubBytes
    for (int i = 0; i < 16; i++) state[i] = SW_SBOX[state[i]];
    // ShiftRows
    uint8_t tmp;
    tmp=state[1]; state[1]=state[5]; state[5]=state[9]; state[9]=state[13]; state[13]=tmp;
    tmp=state[2]; state[2]=state[10]; state[10]=tmp;
    tmp=state[6]; state[6]=state[14]; state[14]=tmp;
    tmp=state[3]; state[3]=state[15]; state[15]=state[11]; state[11]=state[7]; state[7]=tmp;
    // MixColumns (skip on last round)
    if (round < 10) {
      for (int c = 0; c < 4; c++) {
        uint8_t* s = state + c*4;
        uint8_t s0=s[0],s1=s[1],s2=s[2],s3=s[3];
        s[0] = sw_gmul(0x02,s0)^sw_gmul(0x03,s1)^s2^s3;
        s[1] = s0^sw_gmul(0x02,s1)^sw_gmul(0x03,s2)^s3;
        s[2] = s0^s1^sw_gmul(0x02,s2)^sw_gmul(0x03,s3);
        s[3] = sw_gmul(0x03,s0)^s1^s2^sw_gmul(0x02,s3);
      }
    }
    // AddRoundKey
    for (int i = 0; i < 16; i++) state[i] ^= rk[round*16+i];
  }
  memcpy(out, state, 16);
}

// ═══════════════════════════════════════════════════════════════════════════
// BENCHMARK FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

long runSwBenchmark() {
  AesRoundKey rk;
  swAesKeyExpansion(TEST_KEY, rk);
  uint8_t out[16];

  // Warm up
  for (int i = 0; i < BENCH_WARMUP; i++) {
    swAesEncryptBlock(rk, TEST_PLAIN, out);
    yield();
  }

  serialLine("[AES-SW]  Running " + String(BENCH_ITERATIONS) + " iterations...");
  int64_t t_start = esp_timer_get_time();
  for (int i = 0; i < BENCH_ITERATIONS; i++) {
    swAesEncryptBlock(rk, TEST_PLAIN, out);
  }
  int64_t t_end = esp_timer_get_time();

  long total_us = (long)(t_end - t_start);
  long avg_us   = total_us / BENCH_ITERATIONS;
  serialLine("[AES-SW]  Total: " + String(total_us) + " µs  →  avg: " + String(avg_us) + " µs/block");

  // Verify first output matches FIPS 197 expected ciphertext
  uint8_t expected[16] = {0x39,0x25,0x84,0x1d,0x02,0xdc,0x09,0xfb,0xdc,0x11,0x85,0x97,0x19,0x6a,0x0b,0x32};
  bool ok = (memcmp(out, expected, 16) == 0);
  serialLine(String("[AES-SW]  Correctness check: ") + (ok ? "PASS ✓" : "FAIL ✗  — check SW implementation"));

  return avg_us;
}

long runHwBenchmark() {
  esp_aes_context ctx;
  esp_aes_init(&ctx);
  esp_aes_setkey(&ctx, TEST_KEY, 128);
  uint8_t out[16];

  // Warm up
  for (int i = 0; i < BENCH_WARMUP; i++) {
    esp_aes_crypt_ecb(&ctx, ESP_AES_ENCRYPT, TEST_PLAIN, out);
    yield();
  }

  serialLine("[AES-HW]  Running " + String(BENCH_ITERATIONS) + " iterations...");
  int64_t t_start = esp_timer_get_time();
  for (int i = 0; i < BENCH_ITERATIONS; i++) {
    esp_aes_crypt_ecb(&ctx, ESP_AES_ENCRYPT, TEST_PLAIN, out);
  }
  int64_t t_end = esp_timer_get_time();
  esp_aes_free(&ctx);

  long total_us = (long)(t_end - t_start);
  long avg_us   = total_us / BENCH_ITERATIONS;
  serialLine("[AES-HW]  Total: " + String(total_us) + " µs  →  avg: " + String(avg_us) + " µs/block");

  // Verify against FIPS 197 expected
  uint8_t expected[16] = {0x39,0x25,0x84,0x1d,0x02,0xdc,0x09,0xfb,0xdc,0x11,0x85,0x97,0x19,0x6a,0x0b,0x32};
  bool ok = (memcmp(out, expected, 16) == 0);
  serialLine(String("[AES-HW]  Correctness check: ") + (ok ? "PASS ✓" : "FAIL ✗  — HW AES may not be enabled"));

  return avg_us;
}

void runBenchmarks() {
  serialLine("");
  serialLine("══════════════════════════════════════════");
  serialLine("  AES-128 Hardware/Software Benchmark");
  serialLine("══════════════════════════════════════════");
  serialLine("[AES-SW]  Warming up (" + String(BENCH_WARMUP) + " iterations)...");
  g_sw_us = runSwBenchmark();
  delay(100);
  serialLine("[AES-HW]  Warming up (" + String(BENCH_WARMUP) + " iterations)...");
  g_hw_us = runHwBenchmark();

  if (g_hw_us > 0) {
    g_speedup = (float)g_sw_us / (float)g_hw_us;
  } else {
    g_speedup = 0.0f;
    serialLine("[WARN] HW time is 0 — hardware AES may not have been enabled");
  }

  serialLine("──────────────────────────────────────────");
  serialLine("  RESULTS:");
  serialLine("  SW AES-128 : " + String(g_sw_us) + " µs/block");
  serialLine("  HW AES-128 : " + String(g_hw_us) + " µs/block");
  serialLine("  Speedup    : " + String(g_speedup, 1) + "×");
  serialLine("──────────────────────────────────────────");

  if (g_speedup < 2.0f) {
    serialLine("[WARN] Speedup < 2× — expected 50-200×. Possible causes:");
    serialLine("       - Arduino-ESP32 version not enabling hardware AES");
    serialLine("       - Board selection: must be 'ESP32 Dev Module'");
  }

  serialLine("");
  serialLine("  CPU utilization at 1 packet/200ms:");
  serialLine("  SW: " + String((float)g_sw_us / 200000.0f * 100.0f, 3) + "% per 200ms interval");
  serialLine("  HW: " + String((float)g_hw_us / 200000.0f * 100.0f, 4) + "% per 200ms interval");
  serialLine("══════════════════════════════════════════");

  g_benchDone = true;

  // Publish immediately if connected
  if (mqtt.connected() && g_slot > 0) {
    publishHwAnswer();
    publishBenchTelemetry();
  } else {
    serialLine("[MQTT] Not yet connected — will auto-submit when slot is assigned");
  }

  // Print reflection prompt
  serialLine("");
  serialLine("╔══════════════════════════════════════════╗");
  serialLine("║  Lab Question q_lab2 — Type your answer  ║");
  serialLine("║  then press Enter to submit via MQTT.    ║");
  serialLine("╠══════════════════════════════════════════╣");
  serialLine("║ Q: Based on your measured speedup of     ║");
  serialLine("║    ~" + String((int)g_speedup) + "×, at what packet rate does HW     ║");
  serialLine("║    AES become justified? Show reasoning. ║");
  serialLine("║    Also name one overhead the benchmark  ║");
  serialLine("║    does NOT capture.                     ║");
  serialLine("╚══════════════════════════════════════════╝");
  serialLine("Type your answer (one line) and press Enter:");
}

// ── Serial command interface ──────────────────────────────────────────────────
void printStatus() {
  serialLine("=== CECS 460 Lab 11 Status ===");
  serialLine("FW        : " FW_VERSION " (" FW_DATE ")");
  serialLine("Device ID : " + g_deviceId);
  serialLine("MAC       : " + g_mac);
  serialLine("Slot      : " + (g_slot > 0 ? String(g_slot) : String("unassigned")));
  serialLine("Token     : " + (g_token.length() ? g_token : String("none")));
  serialLine("Student   : " + (g_studentId.length() ? g_studentId : String("none")));
  serialLine("Wi-Fi     : " + String(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected"));
  if (WiFi.status() == WL_CONNECTED) {
    serialLine("IP        : " + WiFi.localIP().toString());
    serialLine("RSSI      : " + String(WiFi.RSSI()) + " dBm");
  }
  serialLine("MQTT      : " + String(mqtt.connected() ? "Connected" : "Disconnected"));
  serialLine("Bench done: " + String(g_benchDone ? "YES" : "NO"));
  if (g_benchDone) {
    serialLine("SW AES    : " + String(g_sw_us) + " µs/block");
    serialLine("HW AES    : " + String(g_hw_us) + " µs/block");
    serialLine("Speedup   : " + String(g_speedup, 1) + "×");
  }
  serialLine("q_lab1 OK : " + String(g_hwAnswerOk ? "YES" : "NO"));
  serialLine("q_lab2 OK : " + String(g_labAnswered ? "YES" : "NO"));
  serialLine("Verbose   : " + String(g_verbose ? "ON" : "OFF"));
  serialLine("==============================");
}

void handleSerialCommand(const String& raw) {
  String cmd = raw; cmd.trim();
  if (!cmd.length()) return;

  // If benchmark is done and this is not a known command, treat as reflection answer
  if (g_benchDone && !g_labAnswered) {
    if (cmd != "help" && cmd != "status" && cmd != "version" &&
        !cmd.startsWith("set ") && cmd != "clear assignment" &&
        !cmd.startsWith("verbose") && cmd != "bench") {
      serialLine("[q_lab2] Submitting answer: \"" + cmd + "\"");
      publishReflectionAnswer(cmd);
      return;
    }
  }

  serialLine("> " + cmd);

  if (cmd == "help") {
    serialLine("Commands: help, status, version, bench, verbose on/off");
    serialLine("  set ssid/pass/student/device <val>, clear assignment");
    if (g_benchDone && !g_labAnswered)
      serialLine("  (any other input is submitted as your q_lab2 reflection answer)");
  }
  else if (cmd == "status")         { printStatus(); }
  else if (cmd == "version")        { serialLine("FW: " FW_VERSION " " FW_DATE); }
  else if (cmd == "bench")          { g_benchDone=false; g_hwAnswerOk=false; runBenchmarks(); }
  else if (cmd == "verbose on")     { g_verbose=true;  savePrefBool("verbose",true);  serialLine("Verbose: ON"); }
  else if (cmd == "verbose off")    { g_verbose=false; savePrefBool("verbose",false); serialLine("Verbose: OFF"); }
  else if (cmd == "clear assignment") { clearAssignment(); }
  else if (cmd.startsWith("set ssid "))    { g_ssid=cmd.substring(9);    savePref("ssid",g_ssid);        serialLine("SSID: "+g_ssid); }
  else if (cmd.startsWith("set pass "))    { g_pass=cmd.substring(9);    savePref("pass",g_pass);        serialLine("Pass updated"); }
  else if (cmd.startsWith("set student ")) { g_studentId=cmd.substring(12); savePref("student",g_studentId); serialLine("Student: "+g_studentId); }
  else if (cmd.startsWith("set device "))  { g_deviceId=cmd.substring(11); savePref("deviceId",g_deviceId); serialLine("Device: "+g_deviceId); }
  else {
    serialLine("Unknown command (type 'help')");
  }
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200); delay(200);
  pinMode(LED_PIN, OUTPUT); digitalWrite(LED_PIN, LOW);

  serialLine("");
  serialLine("╔══════════════════════════════════════════╗");
  serialLine("║  CECS 460 Lab 11 — AES Co-Design Bench  ║");
  serialLine("║  Firmware v" FW_VERSION "  " FW_DATE "              ║");
  serialLine("╚══════════════════════════════════════════╝");

  g_mac = getMac();
  loadPrefs();
  if (!g_deviceId.length()) {
    g_deviceId = "esp32_" + g_mac.substring(6);
    savePref("deviceId", g_deviceId);
  }
  serialLine("[Boot] MAC: " + g_mac + "  Device: " + g_deviceId);
  if (g_slot > 0) serialLine("[Boot] Saved slot: " + String(g_slot));

  // MQTT init
  mqtt.setServer(g_mqttHost.c_str(), g_mqttPort);
  mqtt.setCallback(mqttCallback);
  mqtt.setKeepAlive(60);
  mqtt.setSocketTimeout(10);

  serialLine("[Boot] Ready — connecting to network, then running benchmark.");
  serialLine("[Boot] Type 'help' for commands.");
}

// ── Loop ──────────────────────────────────────────────────────────────────────
// Benchmark runs once after first MQTT connection is established.
// This ensures slot assignment is received before the hw answer is auto-submitted.
static bool g_benchScheduled = false;
static bool g_benchTriggered = false;

void loop() {
  // Serial input
  if (Serial.available()) {
    static String buf;
    while (Serial.available()) {
      char c = Serial.read();
      if (c == '\n' || c == '\r') {
        if (buf.length()) { handleSerialCommand(buf); buf = ""; }
      } else { buf += c; }
    }
  }

  checkWifi();

  if (WiFi.status() == WL_CONNECTED) {
    checkMqtt();
    if (mqtt.connected()) {
      mqtt.loop();
      if (!g_announced) announce();

      // Schedule benchmark for first run after connection
      if (!g_benchTriggered && !g_benchDone) {
        static unsigned long benchDelay = 0;
        if (benchDelay == 0) benchDelay = millis();
        // Wait 3 seconds after MQTT connect so announce/assign can complete
        if (millis() - benchDelay > 3000) {
          g_benchTriggered = true;
          runBenchmarks();
        }
      }

      // If benchmark completed while offline, submit now
      if (g_benchDone && !g_hwAnswerOk && g_slot > 0) {
        publishHwAnswer();
      }
    }
  }

  // Heartbeat
  unsigned long now = millis();
  if (now - g_lastHB >= HEARTBEAT_MS) {
    g_lastHB = now;
    publishStatus();
  }

  // Benchmark telemetry (continuous while bench is done)
  if (now - g_lastBenchPub >= BENCH_PUBLISH_MS) {
    g_lastBenchPub = now;
    if (g_benchDone) publishBenchTelemetry();
  }

  // LED: slow blink if bench not done, steady if done and submitted
  static unsigned long ledNext = 0;
  static bool ledOn = false;
  if (!g_benchDone) {
    if (now - ledNext > 500) { ledOn = !ledOn; digitalWrite(LED_PIN, ledOn); ledNext = now; }
  } else if (g_hwAnswerOk && g_labAnswered) {
    digitalWrite(LED_PIN, HIGH);  // both answers in — solid ON
  } else {
    if (now - ledNext > 100) { ledOn = !ledOn; digitalWrite(LED_PIN, ledOn); ledNext = now; }  // fast blink waiting for q_lab2
  }
}
