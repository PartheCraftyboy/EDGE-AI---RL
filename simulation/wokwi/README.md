# 🌐 Online ESP32-S3 Simulation via Wokwi

You can simulate the **M5Stamp ESP32-S3 Reinforcement Learning Edge Node** directly in your browser without any physical hardware!

---

## ⚡ Quick Fix for "Board not found" in Wokwi

Wokwi's component registry has native models for microcontrollers (`board-esp32-s3-devkitc-1`), but does **not** have physical 3D canvas parts named `board-bme680` or `board-ina219`.

Instead, our Wokwi simulation uses:
1. **ESP32-S3 DevKit**: Runs the real Xtensa Dual-Core firmware and Tabular RL Q-table evaluation.
2. **Interactive Red Button ("Simulate Fire Spike")**: Connected to GPIO 0. Pressing it injects an immediate fire/gas spike into the firmware.
3. **Alarm LED**: Connected to GPIO 21. Lights up red when the RL agent triggers an emergency alert!
4. **Autonomous Sensor & Battery Simulation**: The firmware code automatically simulates realistic ambient thermal drift, BME680 VOC gas resistance, and LiFePO4 battery discharge cycles when no physical I2C chips are attached.

---

## 🚀 How to Run in Wokwi (1-Minute Setup)

1. Navigate to: **[https://wokwi.com/projects/new/esp32-s3](https://wokwi.com/projects/new/esp32-s3)**
2. Replace the contents of the tabs:

### 1️⃣ `diagram.json` tab:
Replace everything with:
```json
{
  "version": 1,
  "author": "RL Edge AI Fire & Gas Team",
  "editor": "wokwi",
  "parts": [
    {
      "type": "board-esp32-s3-devkitc-1",
      "id": "esp",
      "top": 0,
      "left": 0,
      "attrs": { "flashSize": "8" }
    },
    {
      "type": "wokwi-pushbutton",
      "id": "btn_fire",
      "top": 120,
      "left": 180,
      "attrs": { "color": "red", "label": "Simulate Fire Spike" }
    },
    {
      "type": "wokwi-led",
      "id": "led_alarm",
      "top": 30,
      "left": 180,
      "attrs": { "color": "red", "label": "Fire Alarm LED" }
    }
  ],
  "connections": [
    [ "esp:0", "btn_fire:2.1", "orange", [ "v0" ] ],
    [ "esp:GND.1", "btn_fire:1.1", "black", [ "v10" ] ],
    [ "esp:21", "led_alarm:A", "red", [ "v0" ] ],
    [ "esp:GND.1", "led_alarm:C", "black", [ "v0" ] ]
  ],
  "dependencies": {}
}
```

### 2️⃣ `sketch.ino` tab:
Copy and paste the full contents of `simulation/wokwi/sketch.ino`.

### 3️⃣ `q_table_export.h` tab:
Click the small downward arrow next to the tabs $\rightarrow$ Click **New File** $\rightarrow$ Name it `q_table_export.h`.  
Paste the contents of `simulation/wokwi/q_table_export.h`.

### 4️⃣ `libraries.txt` tab:
Add a tab named `libraries.txt` (or edit the existing one) with:
```
Adafruit BME680 Library
Adafruit INA219
Adafruit Unified Sensor
ArduinoJson
```

---

## ▶️ Running & Testing

1. Click the green **Play** button.
2. Watch the **Serial Monitor**:
   - The ESP32 boots up and initializes.
   - It computes the environmental state index (e.g. State 02).
   - The RL Policy queries the Q-table and selects `NORMAL_CYCLE` (60s deep sleep).
3. **Simulate a Fire Hazard**:
   - Click and hold the **Red Pushbutton** on the canvas.
   - The serial monitor logs:
     ```
     >>> [EVENT] Wokwi Red Button Pressed! INJECTING FIRE HAZARD! <<<
     RL State Index:  53 / 54
     Selected Action: [3] EMERGENCY_ALERT
     >>> [ALARM] FIRE / TOXIC GAS DETECTED! DISPATCHING EMERGENCY ALERT! <<<
     [Wi-Fi] Connecting to 'Wokwi-GUEST'...
     ```
   - The **Red Alarm LED** lights up immediately!
