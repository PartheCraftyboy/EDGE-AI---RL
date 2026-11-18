#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>

// --- Hardware Pin Definitions ---
#define GAS_SENSOR_PIN      1   // Analog ADC for MQ Gas Sensor
#define TEMP_SENSOR_PIN     2   // Analog ADC for NTC Temperature Sensor
#define BATTERY_POT_PIN     3   // Analog ADC for LiFePO4 Fuel Gauge (INA219)
#define SIM_BUTTON_PIN      0   // Pushbutton on GPIO 0
#define ALARM_LED_PIN       21  // Red Alarm LED on GPIO 21

// --- Wi-Fi & MQTT Broker Configuration ---
#define WIFI_SSID           "Wokwi-GUEST"
#define WIFI_PASSWORD       ""
#define MQTT_BROKER         "broker.hivemq.com"
#define MQTT_PORT           1883
#define MQTT_TOPIC          "rl-edge-fire-gas/kalki/telemetry"

// --- Debug switch: force telemetry on EVERY boot cycle while testing ---
// Set to false once you've confirmed the Wokwi -> broker -> backend chain works,
// to restore the original 1-in-10 power-saving behavior.
#define TELEMETRY_EVERY_BOOT true

// --- Battery Chemistry Parameters (1S LiFePO4) ---
#define BATTERY_NOMINAL_V   3.20f
#define BATTERY_MAX_V       3.65f
#define BATTERY_CUTOFF_V    2.50f

// --- Action Mapping ---
const uint64_t ACTION_SLEEP_SEC[4] = { 600, 60, 10, 2 };
const char* ACTION_NAMES[4] = {
  "DEEP_SLEEP_LONG",
  "NORMAL_CYCLE",
  "ELEVATED_SCAN",
  "EMERGENCY_ALERT"
};

// --- RTC Fast Memory (Persists across ESP32 Deep Sleep) ---
RTC_DATA_ATTR int boot_count = 0;
RTC_DATA_ATTR float rtc_last_gas = 45.0f;
RTC_DATA_ATTR float rtc_last_temp = 25.0f;
RTC_DATA_ATTR uint64_t rtc_last_sleep_sec = 60;

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// ============================================================================
// EMBEDDED REINFORCEMENT LEARNING Q-TABLE (54 States x 4 Actions)
// ============================================================================
#define NUM_STATES 54
#define NUM_ACTIONS 4

static const float Q_TABLE[NUM_STATES][NUM_ACTIONS] = {
    /* State 00 */ { 11.5013f, 117.8365f, 16.1509f, -41.9884f },
    /* State 01 */ { -26.2744f, 76.7275f, 14.9415f, -52.7459f },
    /* State 02 */ { -87.2598f, 110.1532f, 12.3490f, -54.1991f },
    /* State 03 */ { -96.9909f, 20.3246f, 0.8860f, -10.0311f },
    /* State 04 */ { -111.7715f, 25.3881f, 5.3813f, 0.0000f },
    /* State 05 */ { -0.0455f, 27.2087f, 7.8493f, -24.0378f },
    /* State 06 */ { -616.1091f, 172.9826f, 345.6680f, 126.1645f },
    /* State 07 */ { -646.6197f, 178.1350f, 318.5902f, 74.8528f },
    /* State 08 */ { -566.5535f, 220.0883f, 345.7772f, 188.3009f },
    /* State 09 */ { 0.0000f, 0.0000f, 67.3160f, 0.0000f },
    /* State 10 */ { 0.0000f, 0.1304f, 114.7084f, 0.0000f },
    /* State 11 */ { 0.0000f, 0.0000f, 65.4534f, 0.0000f },
    /* State 12 */ { -493.5588f, 310.7688f, 395.3460f, 437.5143f },
    /* State 13 */ { -594.4587f, 329.3897f, 286.5655f, 422.5137f },
    /* State 14 */ { -488.4394f, 319.2120f, 374.5836f, 437.7719f },
    /* State 15 */ { -540.2508f, 95.4204f, 147.7372f, 437.4554f },
    /* State 16 */ { -438.1631f, 111.0050f, 154.7337f, 430.4518f },
    /* State 17 */ { -492.0643f, 94.4162f, 201.1484f, 452.3612f },
    /* State 18 */ { 37.6160f, 37.7275f, 39.7168f, -5.5781f },
    /* State 19 */ { -28.1054f, 38.7811f, 39.7630f, -3.7578f },
    /* State 20 */ { 37.9419f, 37.7323f, 39.7168f, -6.9613f },
    /* State 21 */ { 5.6372f, 0.0000f, 24.2509f, 0.0000f },
    /* State 22 */ { 4.2089f, 5.2755f, 42.1049f, 0.0000f },
    /* State 23 */ { 4.5059f, 1.1359f, 18.3964f, 0.0000f },
    /* State 24 */ { -227.5893f, 178.7409f, 6.2825f, -5.6842f },
    /* State 25 */ { -391.1387f, 40.8579f, 280.4727f, 3.3571f },
    /* State 26 */ { -257.2621f, 212.1017f, 31.3522f, 39.4536f },
    /* State 27 */ { 0.0000f, 0.0000f, 5.0000f, 0.0000f },
    /* State 28 */ { 0.0000f, 0.0000f, 5.3808f, 0.0000f },
    /* State 29 */ { 0.0000f, 0.0000f, 5.4431f, 0.0000f },
    /* State 30 */ { -83.1339f, 241.7333f, 0.0000f, 91.4593f },
    /* State 31 */ { -280.8790f, 117.9824f, 32.5773f, 364.2987f },
    /* State 32 */ { -98.8484f, 79.9208f, 54.7792f, 248.3534f },
    /* State 33 */ { 0.0000f, 0.0000f, 0.0000f, 10.0000f },
    /* State 34 */ { 0.0000f, 35.2506f, 33.8730f, 331.9939f },
    /* State 35 */ { 0.0000f, 0.0000f, 0.0000f, 106.4297f },
    /* State 36 */ { -626.3936f, 23.1368f, 141.9631f, 389.9312f },
    /* State 37 */ { -696.0869f, 88.8647f, 156.7773f, 306.6654f },
    /* State 38 */ { -688.8481f, 66.1544f, 85.2195f, 384.7830f },
    /* State 39 */ { 0.0000f, 0.0000f, 0.0000f, 60.2956f },
    /* State 40 */ { 0.0000f, 0.0000f, 0.0000f, 10.0000f },
    /* State 41 */ { 0.0000f, 0.0000f, 0.0000f, 104.7673f },
    /* State 42 */ { -504.3635f, 238.2120f, 338.0759f, 420.5605f },
    /* State 43 */ { -509.0918f, 209.7004f, 311.0768f, 410.5188f },
    /* State 44 */ { -526.4880f, 207.2432f, 327.0380f, 411.4563f },
    /* State 45 */ { -365.1672f, 147.3367f, 290.4607f, 425.6793f },
    /* State 46 */ { -379.4213f, 162.9453f, 197.9799f, 416.7178f },
    /* State 47 */ { -216.8101f, 148.6380f, 291.4262f, 420.5988f },
    /* State 48 */ { -564.1559f, 244.3449f, 320.3747f, 353.8559f },
    /* State 49 */ { -580.6471f, 235.7504f, 303.6671f, 346.2602f },
    /* State 50 */ { -569.0326f, 228.0534f, 314.7803f, 355.1657f },
    /* State 51 */ { -552.3867f, 40.3282f, 146.7589f, 355.6709f },
    /* State 52 */ { -507.9202f, 74.6917f, 194.5364f, 346.7182f },
    /* State 53 */ { -538.2954f, 61.4318f, 111.3410f, 356.3473f },
};

int get_rl_action(int state_idx) {
    if (state_idx < 0 || state_idx >= NUM_STATES) return 1;
    int best_a = 0;
    float max_q = Q_TABLE[state_idx][0];
    for (int a = 1; a < NUM_ACTIONS; a++) {
        if (Q_TABLE[state_idx][a] > max_q) {
            max_q = Q_TABLE[state_idx][a];
            best_a = a;
        }
    }
    return best_a;
}

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

// Human-readable WiFi status, since WiFi.status() alone is just a number
const char* wifi_status_to_string(wl_status_t status) {
    switch (status) {
        case WL_IDLE_STATUS:     return "IDLE_STATUS (not yet started)";
        case WL_NO_SSID_AVAIL:   return "NO_SSID_AVAIL (SSID not found)";
        case WL_SCAN_COMPLETED:  return "SCAN_COMPLETED";
        case WL_CONNECTED:       return "CONNECTED";
        case WL_CONNECT_FAILED:  return "CONNECT_FAILED (wrong password/auth)";
        case WL_CONNECTION_LOST: return "CONNECTION_LOST";
        case WL_DISCONNECTED:    return "DISCONNECTED";
        default:                 return "UNKNOWN";
    }
}

// Human-readable PubSubClient connect() return code
const char* mqtt_rc_to_string(int rc) {
    switch (rc) {
        case -4: return "MQTT_CONNECTION_TIMEOUT (server didn't respond in time)";
        case -3: return "MQTT_CONNECTION_LOST (network connection broke)";
        case -2: return "MQTT_CONNECT_FAILED (couldn't reach broker.hivemq.com:1883 - network/firewall issue)";
        case -1: return "MQTT_DISCONNECTED (clean disconnect)";
        case  0: return "MQTT_CONNECTED";
        case  1: return "MQTT_CONNECT_BAD_PROTOCOL";
        case  2: return "MQTT_CONNECT_BAD_CLIENT_ID (broker rejected the client ID)";
        case  3: return "MQTT_CONNECT_UNAVAILABLE (broker refused the connection)";
        case  4: return "MQTT_CONNECT_BAD_CREDENTIALS";
        case  5: return "MQTT_CONNECT_UNAUTHORIZED";
        default: return "UNKNOWN_RC";
    }
}

void transmit_telemetry(float temp, float gas_kohm, float v_bat, float soc_pct, int action, bool is_alert) {
    Serial.printf("\n[Wi-Fi] Connecting to '%s'...\n", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    const unsigned long WIFI_TIMEOUT_MS = 15000; // was 6000 - too tight for Wokwi-GUEST
    unsigned long start_attempt = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start_attempt < WIFI_TIMEOUT_MS) {
        delay(250);
        Serial.print(".");
    }

    if (WiFi.status() != WL_CONNECTED) {
        Serial.printf("\n[Wi-Fi] Connection timed out after %lums. Status: %s\n",
                      WIFI_TIMEOUT_MS, wifi_status_to_string(WiFi.status()));
        return;
    }

    Serial.println("\n[Wi-Fi] Connected! IP: " + WiFi.localIP().toString());
    Serial.printf("[MQTT] Connecting to %s:%d ...\n", MQTT_BROKER, MQTT_PORT);
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setSocketTimeout(10);

    String clientId = "Wokwi-ESP32-S3-" + String(random(0xffff), HEX);

    const int MAX_MQTT_ATTEMPTS = 3;
    bool connected = false;
    for (int attempt = 1; attempt <= MAX_MQTT_ATTEMPTS && !connected; attempt++) {
        Serial.printf("[MQTT] Attempt %d/%d with client ID '%s'...\n",
                      attempt, MAX_MQTT_ATTEMPTS, clientId.c_str());
        connected = mqttClient.connect(clientId.c_str());
        if (!connected) {
            Serial.printf("[MQTT] Failed: %s\n", mqtt_rc_to_string(mqttClient.state()));
            delay(1000);
        }
    }

    if (!connected) {
        Serial.println("[MQTT] Giving up after max attempts this cycle.");
        WiFi.disconnect(true);
        WiFi.mode(WIFI_OFF);
        return;
    }

    String json = "{";
    json += "\"device_id\":\"m5stamp-s3-wokwi\",";
    json += "\"boot_count\":" + String(boot_count) + ",";
    json += "\"fire_alert\":" + String(is_alert ? "true" : "false") + ",";
    json += "\"temperature_c\":" + String(temp, 2) + ",";
    json += "\"gas_resistance_kohm\":" + String(gas_kohm, 2) + ",";
    json += "\"battery_voltage\":" + String(v_bat, 3) + ",";
    json += "\"battery_soc_pct\":" + String(soc_pct * 100.0f, 1) + ",";
    json += "\"rl_action\":\"" + String(ACTION_NAMES[action]) + "\"";
    json += "}";

    Serial.println("[MQTT] Publishing payload: " + json);
    bool pub_ok = mqttClient.publish(MQTT_TOPIC, json.c_str());
    Serial.printf("[MQTT] publish() returned: %s\n", pub_ok ? "true" : "false");

    // Give the client a few loop() cycles to actually flush the write and
    // handle the keepalive ping before we yank the connection down.
    for (int i = 0; i < 10; i++) {
        mqttClient.loop();
        delay(30);
    }

    mqttClient.disconnect();
    Serial.println("[MQTT] Disconnected cleanly.");

    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);
}

void setup() {
    Serial.begin(115200);
    delay(500);
    boot_count++;

    pinMode(SIM_BUTTON_PIN, INPUT_PULLUP);
    pinMode(ALARM_LED_PIN, OUTPUT);
    digitalWrite(ALARM_LED_PIN, LOW);

    Serial.println("\n========================================================");
    Serial.println("  M5Stamp ESP32-S3 RL Edge AI Fire & Gas Node [Wokwi]");
    Serial.printf("  Boot Cycle: #%d | Preserved in RTC RAM\n", boot_count);
    if (TELEMETRY_EVERY_BOOT) {
        Serial.println("  [DEBUG MODE] TELEMETRY_EVERY_BOOT = true -> publishing every cycle");
    }
    Serial.println("========================================================");

    // 1. INA219 Fuel Gauge: Read from LiFePO4 Potentiometer Tool on GPIO 3
    int raw_bat = analogRead(BATTERY_POT_PIN);
    float bus_voltage = BATTERY_CUTOFF_V + (((float)raw_bat / 4095.0f) * (BATTERY_MAX_V - BATTERY_CUTOFF_V));
    bus_voltage = constrain(bus_voltage, BATTERY_CUTOFF_V, BATTERY_MAX_V);
    float soc_pct = (bus_voltage - BATTERY_CUTOFF_V) / (BATTERY_MAX_V - BATTERY_CUTOFF_V);
    soc_pct = constrain(soc_pct, 0.0f, 1.0f);
    Serial.printf("[Battery (INA219)] Voltage: %.3f V | SoC: %.1f%%\n", bus_voltage, soc_pct * 100.0f);

    // 2. Read Environmental Hardware Sensors
    int raw_temp = analogRead(TEMP_SENSOR_PIN);
    int raw_gas = analogRead(GAS_SENSOR_PIN);

    // Temperature calculation from NTC sensor
    float temperature = 24.5f;
    if (raw_temp > 50 && raw_temp < 4050) {
        const float BETA = 3950.0f;
        temperature = 1.0f / (log(1.0f / (4095.0f / (float)raw_temp - 1.0f)) / BETA + 1.0f / 298.15f) - 273.15f;
    } else if (raw_temp >= 4050) {
        temperature = 95.0f;
    }
    temperature = constrain(temperature, -10.0f, 99.0f);

    // Gas Resistance calculation from MQ Gas Sensor
    float gas_ratio = (float)raw_gas / 4095.0f;
    float gas_kohm = 50.0f - (pow(gas_ratio, 1.8f) * 46.0f);
    gas_kohm = constrain(gas_kohm, 2.0f, 55.0f);

    // Pushbutton override for instant fire injection demo
    bool fire_button_pressed = (digitalRead(SIM_BUTTON_PIN) == LOW);
    if (fire_button_pressed) {
        Serial.println("\n>>> [EVENT] Red Button Pressed! INJECTING FIRE HAZARD! <<<");
        temperature = 72.5f;
        gas_kohm = 3.0f;
    }

    Serial.printf("[Sensors] Temp: %.2f C | Gas Resistance: %.2f kOhm\n", temperature, gas_kohm);

    // 3. Compute Derivatives & State Index
    float dt = (float)rtc_last_sleep_sec;
    float gas_deriv = (dt > 0) ? (gas_kohm - rtc_last_gas) / dt : 0.0f;
    int state_idx = compute_state_index(temperature, gas_kohm, gas_deriv, soc_pct);

    // 4. Query RL Policy (Lookup in Q-table)
    int action = get_rl_action(state_idx);

    Serial.println("--------------------------------------------------------");
    Serial.printf("  RL State Index:  %d / 54\n", state_idx);
    Serial.printf("  Selected Action: [%d] %s\n", action, ACTION_NAMES[action]);
    Serial.printf("  Action Sleep:    %llu seconds\n", ACTION_SLEEP_SEC[action]);
    Serial.println("--------------------------------------------------------");

    // 5. Fire Alert & Actuation Logic
    bool is_fire_alert = (action == 3) || (temperature > 50.0f) || (gas_kohm < 10.0f);
    digitalWrite(ALARM_LED_PIN, is_fire_alert ? HIGH : LOW);

    if (is_fire_alert) {
        Serial.println(">>> [ALARM] FIRE / TOXIC GAS DETECTED! DISPATCHING EMERGENCY ALERT! <<<");
        transmit_telemetry(temperature, gas_kohm, bus_voltage, soc_pct, action, true);
    } else if (TELEMETRY_EVERY_BOOT || (boot_count % 10 == 0)) {
        Serial.println("[Heartbeat] Routine periodic telemetry dispatch.");
        transmit_telemetry(temperature, gas_kohm, bus_voltage, soc_pct, action, false);
    } else {
        Serial.println("[Skip] Not a fire alert and not a heartbeat cycle - no transmission this boot.");
    }

    // 6. Save RTC variables
    rtc_last_temp = temperature;
    rtc_last_gas = gas_kohm;
    uint64_t sleep_sec = ACTION_SLEEP_SEC[action];
    rtc_last_sleep_sec = sleep_sec;

    // 7. Enter Deep Sleep (Simulated by Wokwi timer wakeup)
    Serial.printf("[Sleep] Entering Deep Sleep for %llu seconds. Current ~15 uA.\n", sleep_sec);
    Serial.flush();

    uint64_t sim_sleep_us = min(sleep_sec, (uint64_t)5) * 1000000ULL;
    esp_sleep_enable_timer_wakeup(sim_sleep_us);
    esp_deep_sleep_start();
}

void loop() {
    // Never reached: ESP32 resets into setup() upon wakeup
}
