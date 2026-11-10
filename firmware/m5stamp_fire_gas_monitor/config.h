/*
 * Configuration Header for M5Stamp ESP32-S3 Fire & Gas Monitor
 */

#ifndef CONFIG_H
#define CONFIG_H

// --- Wi-Fi Credentials ---
#define WIFI_SSID           "YOUR_WIFI_SSID"
#define WIFI_PASSWORD       "YOUR_WIFI_PASSWORD"
#define WIFI_TIMEOUT_MS     10000

// --- AWS IoT Core / Backend Endpoint ---
// Use either AWS IoT Core MQTT or direct HTTPS REST Endpoint
#define AWS_ENDPOINT        "https://your-api-id.execute-api.us-east-1.amazonaws.com/telemetry"
#define DEVICE_ID           "m5stamp-s3-edge-01"

// --- Hardware Pin Definitions (M5Stamp S3) ---
#define I2C_SDA_PIN         13   // Default M5Stamp S3 SDA
#define I2C_SCL_PIN         15   // Default M5Stamp S3 SCL
#define ONBOARD_BUTTON_PIN  0    // M5Stamp user button
#define ONBOARD_LED_PIN     21   // WS2812 RGB LED Data pin

// --- I2C Addresses ---
#define BME680_I2C_ADDR     0x77 // Or 0x76 depending on SDO pin
#define INA219_I2C_ADDR     0x40 // Default INA219 address

// --- Battery Chemistry Parameters (1S LiFePO4) ---
#define BATTERY_NOMINAL_V   3.20f
#define BATTERY_MAX_V       3.65f
#define BATTERY_CUTOFF_V    2.50f
#define BATTERY_CAPACITY_MAH 600.0f

// --- Hazard Thresholds ---
#define FIRE_TEMP_THRESHOLD_C 50.0f
#define GAS_HAZARD_THRESHOLD_KOHM 12.0f

#endif // CONFIG_H
