/*
 * M5Stamp ESP32-S3: RL-Driven Adaptive Fire & Gas Sensing Edge Node
 * Hardware:
 *   - M5Stamp ESP32-S3 (Xtensa Dual-Core 240MHz)
 *   - SmartElex Bosch BME680 (I2C: Gas, Temp, Hum, Press)
 *   - INA219 Fuel Gauge (I2C: Bus Voltage, Current, Power)
 *   - 1S LiFePO4 Battery (3.2V, 600mAh) + 1S BMS + TP5000 Charger
 *
 * Reinforcement Learning Policy:
 *   - Evaluates Q-Table (q_table_export.h) in RTC fast memory.
 *   - Adaptively balances BME680 micro-hotplate pulses, deep sleep duration,
 *     and Wi-Fi radio power.
 */

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>
#include <Adafruit_INA219.h>
#include "config.h"
#include "q_table_export.h"

// Hardware instances
Adafruit_BME680 bme;
Adafruit_INA219 ina219(INA219_I2C_ADDR);

// RTC Fast Memory: Preserved across ESP32 Deep Sleep cycles
RTC_DATA_ATTR int boot_count = 0;
RTC_DATA_ATTR float rtc_last_gas_resistance = 45.0f;
RTC_DATA_ATTR float rtc_last_temperature = 25.0f;
RTC_DATA_ATTR float rtc_accumulated_mah = 0.0f;
RTC_DATA_ATTR uint64_t rtc_last_sleep_sec = 60;

// Action timing map matching Python training environment
const uint64_t ACTION_SLEEP_SEC[4] = { 600, 60, 10, 2 };
const char* ACTION_NAMES[4] = {
  "DEEP_SLEEP_LONG",
  "NORMAL_CYCLE",
  "ELEVATED_SCAN",
  "EMERGENCY_ALERT"
};

// Discretize inputs into state index (0 to 53)
int compute_state_index(float temp, float gas_kohm, float gas_deriv, float soc_pct) {
  int t_bin = (temp < 35.0f) ? 0 : (temp < 50.0f ? 1 : 2);
  int g_bin = (gas_kohm > 30.0f) ? 0 : (gas_kohm > 10.0f ? 1 : 2);
  int d_bin = (gas_deriv < -0.5f) ? 1 : 0;
  int b_bin = (soc_pct < 0.30f) ? 0 : (soc_pct < 0.70f ? 1 : 2);

  int state_idx = (t_bin * 18) + (g_bin * 6) + (d_bin * 3) + b_bin;
  if (state_idx < 0) state_idx = 0;
  if (state_idx >= NUM_STATES) state_idx = NUM_STATES - 1;
  return state_idx;
}

// Transmit alert or telemetry packet to AWS over Wi-Fi
bool transmit_to_aws(float temp, float gas_kohm, float v_bat, float soc_pct, int action, bool is_alert) {
  Serial.printf("[Wi-Fi] Connecting to %s...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long start_attempt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start_attempt < WIFI_TIMEOUT_MS) {
    delay(100);
    Serial.print(".");
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\n[Wi-Fi] Failed to connect within timeout!");
    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);
    return false;
  }

  Serial.println("\n[Wi-Fi] Connected! IP: " + WiFi.localIP().toString());

  // Formulate JSON telemetry
  String json_payload = "{";
  json_payload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  json_payload += "\"boot_count\":" + String(boot_count) + ",";
  json_payload += "\"fire_alert\":" + String(is_alert ? "true" : "false") + ",";
  json_payload += "\"temperature_c\":" + String(temp, 2) + ",";
  json_payload += "\"gas_resistance_kohm\":" + String(gas_kohm, 2) + ",";
  json_payload += "\"battery_voltage\":" + String(v_bat, 3) + ",";
  json_payload += "\"battery_soc_pct\":" + String(soc_pct * 100.0f, 1) + ",";
  json_payload += "\"rl_action\":\"" + String(ACTION_NAMES[action]) + "\"";
  json_payload += "}";

  Serial.println("[AWS] Dispatching payload: " + json_payload);

  HTTPClient http;
  http.begin(AWS_ENDPOINT);
  http.addHeader("Content-Type", "application/json");
  int http_code = http.POST(json_payload);

  Serial.printf("[AWS] Response Code: %d\n", http_code);
  http.end();

  // Shut down Wi-Fi immediately to conserve battery
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  return (http_code == 200 || http_code == 201);
}

void setup() {
  Serial.begin(115200);
  boot_count++;
  Serial.printf("\n========================================\n");
  Serial.printf(" M5Stamp ESP32-S3 RL Fire & Gas Monitor\n");
  Serial.printf(" Boot Cycle: #%d\n", boot_count);
  Serial.printf("========================================\n");

  // Initialize I2C Bus on configured pins
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);

  // 1. Read Fuel Gauge (INA219)
  float bus_voltage = BATTERY_NOMINAL_V;
  float current_ma = 0.0f;
  if (ina219.begin()) {
    bus_voltage = ina219.getBusVoltage_V();
    current_ma = ina219.getCurrent_mA();
    Serial.printf("[INA219] Bus Voltage: %.3f V | Current Draw: %.2f mA\n", bus_voltage, current_ma);
  } else {
    Serial.println("[WARN] INA219 not detected! Falling back to nominal 3.2V.");
  }

  // Calculate State of Charge (SoC) for LiFePO4
  float soc_pct = (bus_voltage - BATTERY_CUTOFF_V) / (BATTERY_MAX_V - BATTERY_CUTOFF_V);
  soc_pct = constrain(soc_pct, 0.0f, 1.0f);

  // 2. Read BME680 Environmental Sensor
  float temperature = rtc_last_temperature;
  float gas_kohm = rtc_last_gas_resistance;

  if (bme.begin(BME680_I2C_ADDR)) {
    // Configure oversampling and filter
    bme.setTemperatureOversampling(BME680_OS_2X);
    bme.setHumidityOversampling(BME680_OS_1X);
    bme.setPressureOversampling(BME680_OS_NONE);
    bme.setIIRFilterSize(BME680_FILTER_SIZE_3);

    // Pulse micro-hotplate: 320°C for 30 ms
    bme.setGasHeater(320, 30);

    if (bme.performReading()) {
      temperature = bme.temperature;
      gas_kohm = bme.gas_resistance / 1000.0f;
      Serial.printf("[BME680] Temp: %.2f °C | Gas: %.2f kOhm\n", temperature, gas_kohm);
    } else {
      Serial.println("[WARN] BME680 reading failed!");
    }
  } else {
    Serial.println("[WARN] BME680 not detected on I2C bus!");
  }

  // Calculate derivatives
  float dt = (float)rtc_last_sleep_sec;
  float gas_deriv = (dt > 0) ? (gas_kohm - rtc_last_gas_resistance) / dt : 0.0f;

  // 3. Compute State Index and Query RL Policy (Q-Table)
  int state_idx = compute_state_index(temperature, gas_kohm, gas_deriv, soc_pct);
  int action = get_rl_action(state_idx);

  Serial.printf("[RL Policy] State: %d -> Selected Action: [%d] %s\n",
                state_idx, action, ACTION_NAMES[action]);

  // 4. Action Execution
  bool is_fire_alert = (action == 3) || (temperature > FIRE_TEMP_THRESHOLD_C) || (gas_kohm < GAS_HAZARD_THRESHOLD_KOHM);

  // Periodic heartbeat transmission (every 20 cycles) OR immediate hazard alert
  if (is_fire_alert || (boot_count % 20 == 0)) {
    transmit_to_aws(temperature, gas_kohm, bus_voltage, soc_pct, action, is_fire_alert);
  }

  // Save current states to RTC memory before sleep
  rtc_last_temperature = temperature;
  rtc_last_gas_resistance = gas_kohm;
  uint64_t sleep_sec = ACTION_SLEEP_SEC[action];
  rtc_last_sleep_sec = sleep_sec;

  // 5. Enter Ultra-Low-Power Deep Sleep
  Serial.printf("[Sleep] Entering Deep Sleep for %llu seconds. Current will drop to ~15 uA.\n", sleep_sec);
  Serial.flush();

  esp_sleep_enable_timer_wakeup(sleep_sec * 1000000ULL);
  esp_deep_sleep_start();
}

void loop() {
  // Never reached; ESP32 resets into setup() upon timer wake-up
}
