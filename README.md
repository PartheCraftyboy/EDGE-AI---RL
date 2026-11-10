# Reinforcement Learning Edge AI: Fire & Gas Monitoring Node

**Target Microcontroller:** M5Stack M5Stamp ESP32-S3 (Xtensa Dual-Core 240 MHz)  
**Environmental & Gas Sensor:** SmartElex Bosch BME680 (I2C: VOC Gas, Temperature, Humidity, Pressure)  
**Battery & Fuel Gauge:** 1S $\text{LiFePO}_4$ 3.2V 600mAh AA cell + INA219 I2C Current & Voltage Monitor  
**Cloud Backend:** AWS IoT Core + Amazon DynamoDB (Logs) + Amazon SNS (Instant Email Alerting)  
**Local Dashboard:** React 18 + Vite + TailwindCSS + Recharts + FastAPI  

---

## 📁 Repository Structure

```
/home/kalki/RL/
├── README.md                                  # This master guide
├── docs/
│   ├── PROJECT_PROPOSAL_REPORT.pdf           # 📄 Formal Academic PDF Report (Ready to Submit!)
│   ├── PROJECT_PROPOSAL_REPORT.md            # Markdown version of the proposal
│   ├── generate_pdf.py                       # ReportLab PDF compiler script
│   └── figures/
│       ├── energy_comparison.png             # Baseline vs RL energy savings chart
│       └── training_curve.png                # RL policy convergence curve
├── simulation/
│   ├── env.py                                # Custom Gymnasium environment
│   ├── train.py                              # Q-Learning training & evaluation script
│   └── q_table_export.h                      # Exported policy as C header (864 bytes)
├── firmware/
│   └── m5stamp_fire_gas_monitor/
│       ├── m5stamp_fire_gas_monitor.ino      # ESP32-S3 Arduino code (Deep Sleep, I2C, RL, AWS)
│       ├── config.h                          # Wi-Fi, pinout, and threshold definitions
│       └── q_table_export.h                  # On-chip policy matrix
├── cloud/
│   ├── aws_iot_rule.sql                      # AWS IoT Core SQL query rule
│   ├── dynamodb_schema.json                  # DynamoDB table definition
│   └── sns_setup_guide.md                    # Amazon SNS email subscription setup guide
└── dashboard/
    ├── backend/
    │   ├── app.py                            # FastAPI server (reads DynamoDB / simulates live demo)
    │   └── requirements.txt                  # Python dependencies
    └── frontend/
        ├── package.json                      # React dependencies
        ├── vite.config.js                    # Vite configuration
        ├── index.html                        # App entry point
        └── src/
            ├── App.jsx                       # Real-time telemetry dashboard & live graphs
            ├── main.jsx
            └── index.css
```

---

## 🚀 How to Run the Components

### 1. Re-Train the Reinforcement Learning Policy
To re-run the RL simulation and regenerate the charts:
```bash
cd /home/kalki/RL/simulation
uv run --with numpy,matplotlib python3 train.py
```
* Result: Achieves **70.3% energy reduction** over fixed-interval polling. Automatically updates `q_table_export.h` for the ESP32.

### 2. Generate / Rebuild the Documentation PDF
```bash
cd /home/kalki/RL
uv run --with reportlab,pillow python3 docs/generate_pdf.py
```
The compiled PDF is saved to: `docs/PROJECT_PROPOSAL_REPORT.pdf`.

### 3. Run the Local Telemetry Dashboard
In one terminal, start the FastAPI backend:
```bash
cd /home/kalki/RL/dashboard/backend
uv run --with fastapi,uvicorn,boto3 python3 app.py
```
In a second terminal, start the React frontend:
```bash
cd /home/kalki/RL/dashboard/frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.
* Use the **"Simulate Fire Hazard"** button during presentations to demonstrate the RL agent detecting the hazard and triggering emergency mode in real time.

### 4. Flashing the M5Stamp ESP32-S3 (On or before Nov 18th)
1. Open Arduino IDE or PlatformIO.
2. Install libraries:
   * `Adafruit BME680`
   * `Adafruit INA219`
3. Open `firmware/m5stamp_fire_gas_monitor/m5stamp_fire_gas_monitor.ino`.
4. Edit `config.h` with your local Wi-Fi SSID and Password.
5. Select Board: **M5Stamp-S3** (or ESP32S3 Dev Module) and flash via USB-C!
