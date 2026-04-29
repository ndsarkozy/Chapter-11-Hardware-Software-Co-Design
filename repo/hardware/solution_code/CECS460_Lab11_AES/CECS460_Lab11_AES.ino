/*
 * CECS460_Lab11_AES.ino
 * =====================
 * ESP32 classroom firmware for CECS 460
 * Chapter 11 — Hardware/Software Co-Design
 * Hardware: ESP32 DOIT DevKit V1 (30-pin)
 *
 * This sketch does TWO things simultaneously:
 *
 *  [1] THREE-LED TIMING DEMO (visual co-design demonstration)
 *      LED1 — GPIO 18 — 220Ω — GND  (software delayMicroseconds busy-wait)
 *      LED2 — GPIO 19 — 220Ω — GND  (hardware timer ISR)
 *      LED3 — GPIO 21 — 220Ω — GND  (LEDC peripheral, zero CPU after setup)
 *      Serial commands: l=cycle load, +=double freq, -=halve freq, r=reset
 *
 *  [2] SERVER CONNECTION + AES BENCHMARK
 *      WiFi + MQTT — connects to classroom server, gets seat assignment
 *      AES-128 SW vs HW benchmark — auto-submits results via MQTT
 *      Handles q_predict and q_measure free-response submissions
 *
 * The LED demo runs on Core 1 (Arduino loop).
 * WiFi/MQTT/benchmark runs on Core 0 via a FreeRTOS task.
 * Both run simultaneously — the network task never interferes with LED timing.
 *
 * Targets: Arduino-ESP32 core 3.x, DOIT DevKit V1
 * Serial:  115200 baud
 * Version: 2.0.0
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include <esp_system.h>
#include <esp_timer.h>
#include "mbedtls/aes.h"

typedef uint8_t AesRoundKey[176];

#define FW_VERSION        "2.0.0"
#define FW_DATE           "2026-04"

// ── Network defaults ─────────────────────────────────────────────────────────
#define DEFAULT_SSID      "DEEZ"
#define DEFAULT_PASS      "password"
#define DEFAULT_MQTT_HOST "192.168.8.228"
#define DEFAULT_MQTT_PORT 1883
#define HEARTBEAT_MS      10000UL
#define BENCH_PUBLISH_MS  10000UL
#define BUILTIN_LED       2

// ── MQTT topics ──────────────────────────────────────────────────────────────
#define COURSE  "C460"
#define LESSON  "c460_ch11_codesign"
#define NVS_NS  "cecs460"

// ── LED demo pin assignments ─────────────────────────────────────────────────
#define PIN_SW    18   // LED1: software busy-wait
#define PIN_ISR   19   // LED2: hardware timer ISR
#define PIN_LEDC  21   // LED3: LEDC peripheral

// ── Benchmark config ─────────────────────────────────────────────────────────
#define BENCH_ITERATIONS  1000
#define BENCH_WARMUP       10

static const uint8_t TEST_KEY[16] = {
  0x2b,0x7e,0x15,0x16, 0x28,0xae,0xd2,0xa6,
  0xab,0xf7,0x15,0x88, 0x09,0xcf,0x4f,0x3c
};
static const uint8_t TEST_PLAIN[16] = {
  0x32,0x43,0xf6,0xa8, 0x88,0x5a,0x30,0x8d,
  0x31,0x31,0x98,0xa2, 0xe0,0x37,0x07,0x34
};

// ═══════════════════════════════════════════════════════════════════════════════
// SECTION 1 — LED DEMO STATE (Core 1 / loop())
// ═══════════════════════════════════════════════════════════════════════════════

enum LoadLevel { LOAD_NONE=0, LOAD_LIGHT, LOAD_HEAVY, LOAD_BRUTAL, LOAD_COUNT };
static const char* LOAD_NAMES[] = { "NONE", "LIGHT", "HEAVY", "BRUTAL" };

static float     demo_targetHz    = 5.0f;
static uint32_t  demo_halfPeriodUs= 0;
static LoadLevel demo_load        = LOAD_NONE;

static volatile uint32_t sw_toggleCount  = 0;
static volatile uint32_t isr_toggleCount = 0;
static uint32_t sw_lastMeasureUs  = 0;
static uint32_t isr_lastMeasureUs = 0;
static float    sw_measuredHz     = 0.0f;
static float    isr_measuredHz    = 0.0f;

static hw_timer_t* demoTimer = NULL;

void IRAM_ATTR onDemoTimerISR() {
  digitalWrite(PIN_ISR, !digitalRead(PIN_ISR));
  isr_toggleCount++;
}

static void recomputeHalfPeriod() {
  if (demo_targetHz <= 0.0f) demo_targetHz = 1.0f;
  demo_halfPeriodUs = (uint32_t)(500000.0f / demo_targetHz);
}

static void applyTimerFreq() {
  if (demoTimer) timerEnd(demoTimer);
  demoTimer = timerBegin(1000000);               // 1 MHz tick rate (core 3.x)
  timerAttachInterrupt(demoTimer, &onDemoTimerISR);
  timerAlarm(demoTimer, demo_halfPeriodUs, true, 0);
}

static void applyLEDCFreq() {
  ledcDetach(PIN_LEDC);
  ledcAttach(PIN_LEDC, (uint32_t)demo_targetHz, 10);
  ledcWrite(PIN_LEDC, 512);                       // 50% duty, 10-bit res
}

static void applyFrequency() {
  recomputeHalfPeriod();
  applyTimerFreq();
  applyLEDCFreq();
  sw_toggleCount = isr_toggleCount = 0;
  sw_lastMeasureUs = isr_lastMeasureUs = micros();
  sw_measuredHz = isr_measuredHz = 0.0f;
}

static void runDemoLoad(LoadLevel level) {
  switch (level) {
    case LOAD_LIGHT:
      { volatile uint32_t x=0; for(uint32_t i=0;i<50000UL;i++) x+=i*3; (void)x; } break;
    case LOAD_HEAVY:
      { volatile uint32_t x=0; for(uint32_t i=0;i<500000UL;i++) x+=i*3; (void)x; } break;
    case LOAD_BRUTAL:
      { volatile uint32_t x=0; for(uint32_t i=0;i<5000000UL;i++) x+=i*3; (void)x; } break;
    default: break;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// SECTION 2 — NETWORK / BENCHMARK STATE (Core 0 FreeRTOS task)
// ═══════════════════════════════════════════════════════════════════════════════

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

long    g_sw_us      = 0;
long    g_hw_us      = 0;
float   g_speedup    = 0.0f;
bool    g_benchDone  = false;
bool    g_labAnswered= false;
bool    g_hwAnswerOk = false;

// Mutex so Serial prints from Core 0 and Core 1 don't interleave
static SemaphoreHandle_t serialMutex = NULL;

// ── Serial helpers ────────────────────────────────────────────────────────────
void serialLine(const String& s) {
  if (serialMutex) xSemaphoreTake(serialMutex, portMAX_DELAY);
  if (g_prevSameLine) { Serial.println(); g_dotCount=0; g_prevSameLine=false; }
  Serial.println(s);
  if (serialMutex) xSemaphoreGive(serialMutex);
}
void serialDot() {
  if (serialMutex) xSemaphoreTake(serialMutex, portMAX_DELAY);
  Serial.print("."); g_dotCount++;
  g_prevSameLine = true;
  if (g_dotCount >= 60) { Serial.println(); g_dotCount=0; g_prevSameLine=false; }
  if (serialMutex) xSemaphoreGive(serialMutex);
}
void verboseLog(const String& s) { if (g_verbose) serialLine("[DBG] " + s); }

// ── NVS ──────────────────────────────────────────────────────────────────────
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
void savePref    (const String& k, const String& v) { prefs.begin(NVS_NS,false); prefs.putString(k.c_str(),v.c_str()); prefs.end(); }
void savePrefInt (const String& k, int v)            { prefs.begin(NVS_NS,false); prefs.putInt(k.c_str(),v);            prefs.end(); }
void savePrefBool(const String& k, bool v)           { prefs.begin(NVS_NS,false); prefs.putBool(k.c_str(),v);           prefs.end(); }
void clearAssignment() {
  prefs.begin(NVS_NS,false); prefs.remove("slot"); prefs.remove("token"); prefs.end();
  g_slot=-1; g_token=""; g_announced=false; g_labAnswered=false; g_hwAnswerOk=false;
  serialLine("[NVS] Assignment cleared — will re-announce");
}

String getMac() {
  String mac = WiFi.macAddress();
  mac.replace(":",""); mac.toUpperCase();
  return mac;
}

// ── MQTT callback ─────────────────────────────────────────────────────────────
void mqttCallback(char* topic, byte* payload, unsigned int len) {
  String t(topic), p;
  for (unsigned int i=0;i<len;i++) p+=(char)payload[i];
  verboseLog("MQTT RX " + t + " : " + p);

  if (t == String(COURSE)+"/device/assign/"+g_mac) {
    JsonDocument doc;
    if (deserializeJson(doc,p)==DeserializationError::Ok) {
      g_slot  = doc["slot"].as<int>();
      g_token = doc["token"].as<String>();
      String url = doc["student_url"].as<String>();
      savePrefInt("slot",g_slot); savePref("token",g_token);
      serialLine("");
      serialLine("");
      serialLine("╔══════════════════════════════════════════════════════╗");
      serialLine("║           ✓  SEAT ASSIGNED — YOU'RE IN!             ║");
      serialLine("╠══════════════════════════════════════════════════════╣");
      serialLine("║  Seat : " + String(g_slot));
      serialLine("╠══════════════════════════════════════════════════════╣");
      serialLine("║  Open this link in your browser:                    ║");
      serialLine("║                                                      ║");
      serialLine("║  " + url);
      serialLine("║                                                      ║");
      serialLine("║  (Copy the URL above into Chrome / Firefox)         ║");
      serialLine("╚══════════════════════════════════════════════════════╝");
      serialLine("");
      if (g_benchDone && !g_hwAnswerOk)
        serialLine("[MQTT] Benchmark already done — resubmitting...");
    }
  }
  if (t == String(LESSON)+"/control/step") {
    JsonDocument doc;
    if (deserializeJson(doc,p)==DeserializationError::Ok)
      serialLine("[Lesson] Step → " + String(doc["step"].as<int>()));
  }
  if (t == String(LESSON)+"/control/broadcast") {
    JsonDocument doc;
    if (deserializeJson(doc,p)==DeserializationError::Ok)
      serialLine("[Broadcast] " + doc["message"].as<String>());
  }
}

// ── MQTT connect ──────────────────────────────────────────────────────────────
void checkWifi() {
  static bool prev=false;
  bool conn=(WiFi.status()==WL_CONNECTED);
  if(conn&&!prev){ serialLine("[WiFi] Connected! IP:"+WiFi.localIP().toString()+" RSSI:"+String(WiFi.RSSI())+"dBm"); g_mqttBackoff=2000; g_announced=false; }
  else if(!conn&&prev) serialLine("[WiFi] Disconnected");
  prev=conn;
  if(!conn){
    unsigned long now=millis();
    if(now-g_wifiRetry>=8000){ g_wifiRetry=now; serialLine("[WiFi] Connecting to "+g_ssid+"..."); WiFi.mode(WIFI_STA); WiFi.begin(g_ssid.c_str(),g_pass.c_str()); }
  }
}

void checkMqtt() {
  if(WiFi.status()!=WL_CONNECTED) return;
  if(mqtt.connected()){ g_mqttBackoff=2000; return; }
  unsigned long now=millis();
  if(now-g_mqttRetry<(unsigned long)g_mqttBackoff) return;
  g_mqttRetry=now;
  serialLine("[MQTT] Connecting to "+g_mqttHost+":"+String(g_mqttPort)+"...");
  String cid=g_deviceId+"_"+String(random(0xffff),HEX);
  if(mqtt.connect(cid.c_str())){
    serialLine("[MQTT] Connected");
    g_mqttBackoff=2000;
    mqtt.subscribe((String(COURSE)+"/device/assign/"+g_mac).c_str());
    mqtt.subscribe((String(LESSON)+"/control/step").c_str());
    mqtt.subscribe((String(LESSON)+"/control/broadcast").c_str());
    g_announced=false;
  } else {
    serialLine("[MQTT] Failed rc="+String(mqtt.state())+", retry in "+String(g_mqttBackoff/1000)+"s");
    g_mqttBackoff=min(g_mqttBackoff*2,30000);
  }
}

void announce() {
  if(!mqtt.connected()) return;
  JsonDocument doc;
  doc["mac"]=g_mac; doc["device_id"]=g_deviceId; doc["firmware"]=FW_VERSION;
  if(g_slot>0) doc["saved_slot"]=g_slot;
  if(g_token.length()) doc["saved_token"]=g_token;
  if(g_studentId.length()) doc["student_id"]=g_studentId;
  String out; serializeJson(doc,out);
  mqtt.publish((String(COURSE)+"/device/announce").c_str(),out.c_str());
  serialLine("[MQTT] Announce sent (MAC="+g_mac+")");
  g_announced=true;
}

// ── MQTT publish helpers ──────────────────────────────────────────────────────
void publishBenchTelemetry() {
  if(!mqtt.connected()||g_slot<0||!g_benchDone) return;
  JsonDocument doc;
  doc["slot"]=g_slot; doc["sw_us"]=g_sw_us; doc["hw_us"]=g_hw_us;
  doc["speedup"]=g_speedup; doc["blocks"]=BENCH_ITERATIONS; doc["bench_done"]=g_benchDone;
  String out; serializeJson(doc,out);
  mqtt.publish((String(LESSON)+"/"+String(g_slot)+"/bench").c_str(),out.c_str());
  verboseLog("Bench telemetry: "+out);
}

void publishHwAnswer() {
  if(!mqtt.connected()||g_slot<0||!g_benchDone) return;
  char buf[128];
  snprintf(buf,sizeof(buf),"[hw:sw_us=%ld hw_us=%ld speedup=%d blocks=%d]",
           g_sw_us,g_hw_us,(int)g_speedup,BENCH_ITERATIONS);
  JsonDocument doc;
  doc["slot"]=g_slot; doc["token"]=g_token; doc["step"]="q_lab1"; doc["answer"]=String(buf);
  String out; serializeJson(doc,out);
  mqtt.publish((String(LESSON)+"/"+String(g_slot)+"/answer").c_str(),out.c_str());
  serialLine("[MQTT] q_lab1 auto-submitted: "+String(buf));
  g_hwAnswerOk=true;
}

void publishFreeResponse(const String& qid, const String& text) {
  if(!mqtt.connected()||g_slot<0){ serialLine("[MQTT] Not connected — answer not sent"); return; }
  JsonDocument doc;
  doc["slot"]=g_slot; doc["token"]=g_token; doc["step"]=qid; doc["answer"]=text;
  String out; serializeJson(doc,out);
  mqtt.publish((String(LESSON)+"/"+String(g_slot)+"/answer").c_str(),out.c_str());
  serialLine("[MQTT] "+qid+" submitted ("+String(text.length())+" chars)");
  if(qid=="q_lab2") g_labAnswered=true;
}

void publishStatus() {
  if(!mqtt.connected()||g_slot<0) return;
  JsonDocument doc;
  doc["slot"]=g_slot; doc["ip"]=WiFi.localIP().toString(); doc["rssi"]=WiFi.RSSI();
  doc["uptime"]=millis()/1000; doc["firmware"]=FW_VERSION; doc["free_heap"]=ESP.getFreeHeap();
  doc["bench_done"]=g_benchDone;
  if(g_benchDone){ doc["sw_us"]=g_sw_us; doc["hw_us"]=g_hw_us; doc["speedup"]=g_speedup; }
  if(g_studentId.length()) doc["student_id"]=g_studentId;
  String out; serializeJson(doc,out);
  mqtt.publish((String(COURSE)+"/device/status/"+String(g_slot)).c_str(),out.c_str());
  if(g_verbose) serialLine("[HB] "+out); else serialDot();
}

// ═══════════════════════════════════════════════════════════════════════════════
// SOFTWARE AES-128
// ═══════════════════════════════════════════════════════════════════════════════

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
static const uint8_t SW_RCON[11]={0x00,0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1b,0x36};

static uint8_t sw_xtime(uint8_t x){ return (x<<1)^((x&0x80)?0x1b:0x00); }
static uint8_t sw_gmul(uint8_t a,uint8_t b){
  uint8_t p=0;
  for(int i=0;i<8;i++){ if(b&1)p^=a; bool hi=a&0x80; a<<=1; if(hi)a^=0x1b; b>>=1; }
  return p;
}
static void swAesKeyExpansion(const uint8_t* key,AesRoundKey rk){
  memcpy(rk,key,16);
  for(int i=4;i<44;i++){
    uint8_t temp[4]; memcpy(temp,rk+(i-1)*4,4);
    if(i%4==0){ uint8_t t=temp[0]; temp[0]=SW_SBOX[temp[1]]^SW_RCON[i/4]; temp[1]=SW_SBOX[temp[2]]; temp[2]=SW_SBOX[temp[3]]; temp[3]=SW_SBOX[t]; }
    for(int j=0;j<4;j++) rk[i*4+j]=rk[(i-4)*4+j]^temp[j];
  }
}
static void swAesEncryptBlock(const AesRoundKey rk,const uint8_t* in,uint8_t* out){
  uint8_t state[16];
  for(int i=0;i<16;i++) state[i]=in[i]^rk[i];
  for(int round=1;round<=10;round++){
    for(int i=0;i<16;i++) state[i]=SW_SBOX[state[i]];
    uint8_t tmp;
    tmp=state[1];state[1]=state[5];state[5]=state[9];state[9]=state[13];state[13]=tmp;
    tmp=state[2];state[2]=state[10];state[10]=tmp; tmp=state[6];state[6]=state[14];state[14]=tmp;
    tmp=state[3];state[3]=state[15];state[15]=state[11];state[11]=state[7];state[7]=tmp;
    if(round<10){
      for(int c=0;c<4;c++){
        uint8_t* s=state+c*4; uint8_t s0=s[0],s1=s[1],s2=s[2],s3=s[3];
        s[0]=sw_gmul(0x02,s0)^sw_gmul(0x03,s1)^s2^s3;
        s[1]=s0^sw_gmul(0x02,s1)^sw_gmul(0x03,s2)^s3;
        s[2]=s0^s1^sw_gmul(0x02,s2)^sw_gmul(0x03,s3);
        s[3]=sw_gmul(0x03,s0)^s1^s2^sw_gmul(0x02,s3);
      }
    }
    for(int i=0;i<16;i++) state[i]^=rk[round*16+i];
  }
  memcpy(out,state,16);
}

long runSwBenchmark(){
  AesRoundKey rk; swAesKeyExpansion(TEST_KEY,rk); uint8_t out[16];
  for(int i=0;i<BENCH_WARMUP;i++){ swAesEncryptBlock(rk,TEST_PLAIN,out); yield(); }
  serialLine("[AES-SW]  Running "+String(BENCH_ITERATIONS)+" iterations...");
  int64_t t0=esp_timer_get_time();
  for(int i=0;i<BENCH_ITERATIONS;i++) swAesEncryptBlock(rk,TEST_PLAIN,out);
  long avg=(long)(esp_timer_get_time()-t0)/BENCH_ITERATIONS;
  serialLine("[AES-SW]  avg: "+String(avg)+" µs/block");
  return avg;
}

long runHwBenchmark(){
  esp_aes_context ctx; esp_aes_init(&ctx); esp_aes_setkey(&ctx,TEST_KEY,128); uint8_t out[16];
  for(int i=0;i<BENCH_WARMUP;i++){ esp_aes_crypt_ecb(&ctx,ESP_AES_ENCRYPT,TEST_PLAIN,out); yield(); }
  serialLine("[AES-HW]  Running "+String(BENCH_ITERATIONS)+" iterations...");
  int64_t t0=esp_timer_get_time();
  for(int i=0;i<BENCH_ITERATIONS;i++) esp_aes_crypt_ecb(&ctx,ESP_AES_ENCRYPT,TEST_PLAIN,out);
  long avg=(long)(esp_timer_get_time()-t0)/BENCH_ITERATIONS;
  esp_aes_free(&ctx);
  serialLine("[AES-HW]  avg: "+String(avg)+" µs/block");
  return avg;
}

void runBenchmarks(){
  serialLine(""); serialLine("══ AES-128 Benchmark ══");
  g_sw_us=runSwBenchmark(); delay(50);
  g_hw_us=runHwBenchmark();
  g_speedup=(g_hw_us>0)?(float)g_sw_us/(float)g_hw_us:0.0f;
  serialLine("  SW: "+String(g_sw_us)+" µs/block");
  serialLine("  HW: "+String(g_hw_us)+" µs/block");
  serialLine("  Speedup: "+String(g_speedup,1)+"×");
  if(g_speedup<2.0f) serialLine("[WARN] Speedup<2× — check board selection & core version");
  g_benchDone=true;
  if(mqtt.connected()&&g_slot>0){ publishHwAnswer(); publishBenchTelemetry(); }
  else serialLine("[MQTT] Will auto-submit when slot is assigned");
  serialLine("");
  serialLine("╔══════════════════════════════════════════╗");
  serialLine("║  Type your q_predict answer then Enter   ║");
  serialLine("║  (rank the 3 LEDs + explain why)         ║");
  serialLine("╚══════════════════════════════════════════╝");
  serialLine("Or type 'q_measure <your answer>' to submit the observation question.");
}

// ── Status print ──────────────────────────────────────────────────────────────
void printStatus(){
  serialLine("=== CECS 460 Lab 11 v"+String(FW_VERSION)+" ===");
  serialLine("MAC    : "+g_mac);
  serialLine("Slot   : "+(g_slot>0?String(g_slot):String("unassigned")));
  serialLine("WiFi   : "+String(WiFi.status()==WL_CONNECTED?"Connected":"Disconnected"));
  serialLine("MQTT   : "+String(mqtt.connected()?"Connected":"Disconnected"));
  serialLine("Bench  : "+String(g_benchDone?"done":"pending"));
  if(g_benchDone){ serialLine("SW AES : "+String(g_sw_us)+" µs"); serialLine("HW AES : "+String(g_hw_us)+" µs"); serialLine("Speedup: "+String(g_speedup,1)+"×"); }
  serialLine("LED demo: "+String(demo_targetHz,1)+" Hz  LOAD="+String(LOAD_NAMES[demo_load]));
  serialLine("Commands: l=cycle load, +=double freq, -=halve freq, r=reset demo");
  serialLine("          help, status, bench, verbose on/off");
  serialLine("          set ssid/pass/student <val>, clear assignment");
  serialLine("          q_predict <answer>   — submit prediction question");
  serialLine("          q_measure <answer>   — submit observation question");
}

// ── Serial command handler ────────────────────────────────────────────────────
// Shared between both tasks via serialMutex. Called from loop() on Core 1.
static String serialBuf;

void handleSerialCommand(const String& raw){
  String cmd=raw; cmd.trim();
  if(!cmd.length()) return;

  // LED demo single-char commands
  if(cmd.length()==1){
    char c=cmd.charAt(0);
    if(c=='l'){ demo_load=(LoadLevel)((demo_load+1)%LOAD_COUNT); serialLine("Load -> "+String(LOAD_NAMES[demo_load])); return; }
    if(c=='+'){ demo_targetHz*=2.0f; if(demo_targetHz>100000.0f)demo_targetHz=100000.0f; applyFrequency(); serialLine("Freq -> "+String(demo_targetHz,1)+" Hz"); return; }
    if(c=='-'){ demo_targetHz/=2.0f; if(demo_targetHz<0.1f)demo_targetHz=0.1f; applyFrequency(); serialLine("Freq -> "+String(demo_targetHz,1)+" Hz"); return; }
    if(c=='r'){ demo_targetHz=5.0f; demo_load=LOAD_NONE; applyFrequency(); serialLine("Reset -> 5 Hz, LOAD=NONE"); return; }
  }

  // Free-response answer submission
  if(cmd.startsWith("q_predict ")){ publishFreeResponse("q_predict",cmd.substring(10)); return; }
  if(cmd.startsWith("q_measure ")){ publishFreeResponse("q_measure",cmd.substring(10)); return; }

  // If bench done and no known command prefix, treat as q_predict answer (backward compat)
  if(g_benchDone&&!g_labAnswered&&
     cmd!="help"&&cmd!="status"&&cmd!="version"&&cmd!="bench"&&
     !cmd.startsWith("set ")&&cmd!="clear assignment"&&
     !cmd.startsWith("verbose")){
    serialLine("[q_predict] Submitting: \""+cmd+"\"");
    publishFreeResponse("q_predict",cmd);
    g_labAnswered=true;
    return;
  }

  serialLine("> "+cmd);
  if(cmd=="help"||cmd=="status")      { printStatus(); }
  else if(cmd=="version")             { serialLine("FW: "+String(FW_VERSION)+" "+FW_DATE); }
  else if(cmd=="bench")               { g_benchDone=false; g_hwAnswerOk=false; runBenchmarks(); }
  else if(cmd=="verbose on")          { g_verbose=true;  savePrefBool("verbose",true);  serialLine("Verbose: ON"); }
  else if(cmd=="verbose off")         { g_verbose=false; savePrefBool("verbose",false); serialLine("Verbose: OFF"); }
  else if(cmd=="clear assignment")    { clearAssignment(); }
  else if(cmd.startsWith("set ssid "))    { g_ssid=cmd.substring(9);     savePref("ssid",g_ssid);     serialLine("SSID: "+g_ssid); }
  else if(cmd.startsWith("set pass "))    { g_pass=cmd.substring(9);     savePref("pass",g_pass);     serialLine("Pass updated"); }
  else if(cmd.startsWith("set student ")){ g_studentId=cmd.substring(12); savePref("student",g_studentId); serialLine("Student: "+g_studentId); }
  else { serialLine("Unknown command. Type 'help'."); }
}

// ═══════════════════════════════════════════════════════════════════════════════
// CORE 0 TASK — WiFi / MQTT / Benchmark
// Runs independently of loop() so network activity never blocks LED timing
// ═══════════════════════════════════════════════════════════════════════════════

static bool g_benchTriggered = false;

void networkTask(void* pvParameters){
  // Give Arduino setup() time to finish before touching WiFi
  vTaskDelay(pdMS_TO_TICKS(500));

  mqtt.setServer(g_mqttHost.c_str(), g_mqttPort);
  mqtt.setCallback(mqttCallback);
  mqtt.setKeepAlive(60);
  mqtt.setSocketTimeout(10);

  unsigned long benchDelay = 0;

  for(;;){
    checkWifi();
    if(WiFi.status()==WL_CONNECTED){
      checkMqtt();
      if(mqtt.connected()){
        mqtt.loop();
        if(!g_announced) announce();

        if(!g_benchTriggered&&!g_benchDone){
          if(benchDelay==0) benchDelay=millis();
          if(millis()-benchDelay>3000){ g_benchTriggered=true; runBenchmarks(); }
        }
        if(g_benchDone&&!g_hwAnswerOk&&g_slot>0) publishHwAnswer();
      }
    }

    unsigned long now=millis();
    if(now-g_lastHB>=HEARTBEAT_MS)         { g_lastHB=now;       publishStatus(); }
    if(now-g_lastBenchPub>=BENCH_PUBLISH_MS){ g_lastBenchPub=now; if(g_benchDone) publishBenchTelemetry(); }

    // Built-in LED: slow blink=waiting for bench, fast blink=waiting for answer, solid=done
    static unsigned long ledNext=0; static bool ledOn=false;
    if(!g_benchDone){
      if(now-ledNext>500){ ledOn=!ledOn; digitalWrite(BUILTIN_LED,ledOn); ledNext=now; }
    } else if(g_hwAnswerOk&&g_labAnswered){
      digitalWrite(BUILTIN_LED,HIGH);
    } else {
      if(now-ledNext>100){ ledOn=!ledOn; digitalWrite(BUILTIN_LED,ledOn); ledNext=now; }
    }

    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// SETUP & LOOP (Core 1)
// ═══════════════════════════════════════════════════════════════════════════════

void setup(){
  Serial.begin(115200); delay(200);
  serialMutex = xSemaphoreCreateMutex();

  pinMode(BUILTIN_LED, OUTPUT); digitalWrite(BUILTIN_LED, LOW);
  pinMode(PIN_SW,  OUTPUT); digitalWrite(PIN_SW,  LOW);
  pinMode(PIN_ISR, OUTPUT); digitalWrite(PIN_ISR, LOW);

  serialLine("");
  serialLine("╔══════════════════════════════════════════╗");
  serialLine("║  CECS 460 Lab 11 — Co-Design Firmware   ║");
  serialLine("║  v"+String(FW_VERSION)+"  "+FW_DATE+"                     ║");
  serialLine("╠══════════════════════════════════════════╣");
  serialLine("║  LED1(GPIO18) SW   LED2(GPIO19) ISR     ║");
  serialLine("║  LED3(GPIO21) LEDC  All at 5 Hz         ║");
  serialLine("╚══════════════════════════════════════════╝");

  g_mac=getMac();
  loadPrefs();
  if(!g_deviceId.length()){ g_deviceId="esp32_"+g_mac.substring(6); savePref("deviceId",g_deviceId); }
  serialLine("[Boot] MAC: "+g_mac+"  Device: "+g_deviceId);
  if(g_slot>0) serialLine("[Boot] Saved slot: "+String(g_slot));

  // Start LED demo
  applyFrequency();
  sw_lastMeasureUs=isr_lastMeasureUs=micros();

  serialLine("[Boot] LED demo running. Type 'help' for commands.");
  serialLine("[Boot] WiFi/MQTT starting on Core 0...");

  // Launch network task on Core 0, 8KB stack, priority 1
  xTaskCreatePinnedToCore(networkTask, "network", 8192, NULL, 1, NULL, 0);
}

void loop(){
  // ── Serial input ──────────────────────────────────────────────────────────
  while(Serial.available()){
    char c=(char)Serial.read();
    if(c=='\n'||c=='\r'){ if(serialBuf.length()){ handleSerialCommand(serialBuf); serialBuf=""; } }
    else serialBuf+=c;
  }

  // ── Software LED1: busy-wait toggle ──────────────────────────────────────
  uint32_t t0=micros();
  digitalWrite(PIN_SW, HIGH);
  sw_toggleCount++;
  runDemoLoad(demo_load);
  uint32_t elapsed=micros()-t0;
  uint32_t rem=(elapsed<demo_halfPeriodUs)?(demo_halfPeriodUs-elapsed):0;
  if(rem>0) delayMicroseconds(rem);

  t0=micros();
  digitalWrite(PIN_SW, LOW);
  sw_toggleCount++;
  runDemoLoad(demo_load);
  elapsed=micros()-t0;
  rem=(elapsed<demo_halfPeriodUs)?(demo_halfPeriodUs-elapsed):0;
  if(rem>0) delayMicroseconds(rem);

  // ── Measurement windows ───────────────────────────────────────────────────
  uint32_t nowUs=micros();
  uint32_t sw_dt=nowUs-sw_lastMeasureUs;
  if(sw_dt>=1000000UL){
    uint32_t cnt=sw_toggleCount; sw_toggleCount=0; sw_lastMeasureUs=nowUs;
    sw_measuredHz=(cnt/2.0f)/(sw_dt/1e6f);
  }
  uint32_t isr_dt=nowUs-isr_lastMeasureUs;
  if(isr_dt>=1000000UL){
    uint32_t cnt=isr_toggleCount; isr_toggleCount=0; isr_lastMeasureUs=nowUs;
    isr_measuredHz=(cnt/2.0f)/(isr_dt/1e6f);
  }

  // ── 1-second Serial print ─────────────────────────────────────────────────
  static uint32_t lastPrintUs=0;
  if((nowUs-lastPrintUs)>=1000000UL){
    lastPrintUs=nowUs;
    float sw_err =(demo_targetHz>0)?((sw_measuredHz -demo_targetHz)/demo_targetHz*100.0f):0.0f;
    float isr_err=(demo_targetHz>0)?((isr_measuredHz-demo_targetHz)/demo_targetHz*100.0f):0.0f;
    char buf[128];
    snprintf(buf,sizeof(buf),
      "LED1(SW)=%.2f Hz [%.2f%%]   LED2(ISR)=%.2f Hz [%.4f%%]   LED3(LEDC)=locked   LOAD=%s",
      sw_measuredHz,sw_err,isr_measuredHz,isr_err,LOAD_NAMES[demo_load]);
    if(serialMutex) xSemaphoreTake(serialMutex,portMAX_DELAY);
    Serial.println(buf);
    if(serialMutex) xSemaphoreGive(serialMutex);
  }
}
