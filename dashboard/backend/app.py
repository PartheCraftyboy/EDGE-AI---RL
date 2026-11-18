"""
FastAPI Local Backend Proxy for M5Stamp Edge AI Telemetry
Connects to Amazon DynamoDB and serves telemetry endpoints to the local React dashboard.
If AWS credentials are not configured, it gracefully serves realistic simulated edge telemetry
so the dashboard can be demonstrated immediately to professors.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import random

app = FastAPI(title="M5Stamp Edge AI Telemetry API")

# Enable CORS for local React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional DynamoDB client
dynamodb_available = False
table = None
try:
    import boto3
    from boto3.dynamodb.conditions import Key
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('M5Stack_Telemetry')
    # Probe table
    table.table_status
    dynamodb_available = True
    print("[DynamoDB] Connected to AWS DynamoDB successfully!")
except Exception as e:
    print(f"[Notice] Operating in Offline/Demo Mode (Realistic Telemetry Simulator). Reason: {e}")

# In-memory realistic simulated buffer for live demo
simulated_history = []
base_time = int(time.time()) - 1800  # Start 30 mins ago
temp = 24.5
gas_r = 46.2
soc = 98.4

actions = ["DEEP_SLEEP_LONG", "NORMAL_CYCLE", "ELEVATED_SCAN", "EMERGENCY_ALERT"]

for i in range(25):
    t_stamp = base_time + (i * 70)
    # Inject hazard spike at step 20
    is_fire = (i >= 20)
    if is_fire:
        temp += random.uniform(5.5, 9.2)
        gas_r = max(2.1, gas_r - random.uniform(8.0, 12.0))
        action = "EMERGENCY_ALERT"
        soc -= 0.15
    else:
        temp += random.uniform(-0.2, 0.2)
        gas_r += random.uniform(-0.5, 0.5)
        action = random.choice(["DEEP_SLEEP_LONG", "NORMAL_CYCLE"])
        soc -= 0.02
        
    simulated_history.append({
        "device_id": "m5stamp-s3-edge-01",
        "received_at": t_stamp,
        "temperature_c": round(temp, 2),
        "gas_resistance_kohm": round(gas_r, 2),
        "battery_voltage": round(2.5 + (soc / 100.0) * 1.15, 3),
        "battery_soc_pct": round(max(0.0, soc), 1),
        "fire_alert": is_fire,
        "rl_action": action,
        "energy_mJ": 576.0 if action == "EMERGENCY_ALERT" else (1.2 if action == "NORMAL_CYCLE" else 0.05)
    })

# --- Rock-Solid MQTT Bridge: Connects Wokwi directly to Dashboard ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "rl-edge-fire-gas/kalki/telemetry"

try:
    import paho.mqtt.client as mqtt
    import json

    def on_mqtt_connect(client, userdata, flags, rc, properties=None):
        print(f"[MQTT Cloud Bridge] Connected to {MQTT_BROKER}:1883! Subscribed to '{MQTT_TOPIC}'")
        client.subscribe(MQTT_TOPIC)

    def on_mqtt_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            if "received_at" not in payload:
                payload["received_at"] = int(time.time())
            if "energy_mJ" not in payload:
                act = payload.get("rl_action", "NORMAL_CYCLE")
                payload["energy_mJ"] = 576.0 if act == "EMERGENCY_ALERT" else 1.2
            simulated_history.append(payload)
            if len(simulated_history) > 100:
                simulated_history.pop(0)
            print(f">>> [Live Wokwi Telemetry Ingested] Temp: {payload.get('temperature_c')} C | Gas: {payload.get('gas_resistance_kohm')} kOhm | Action: {payload.get('rl_action')}")
        except Exception as err:
            print(f"[MQTT Parse Error] {err}")

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message
    mqtt_client.connect_async(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"[MQTT Warning] Could not start MQTT client: {e}")

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "M5Stamp RL Edge AI Telemetry API",
        "dashboard_ui": "http://localhost:5173",
        "interactive_api_docs": "http://localhost:8000/docs",
        "telemetry_stream": "http://localhost:8000/api/telemetry"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "dynamodb_connected": dynamodb_available,
        "device_target": "m5stamp-s3-edge-01"
    }

@app.get("/api/telemetry")
def get_telemetry(limit: int = 50):
    if dynamodb_available and table:
        try:
            response = table.query(
                KeyConditionExpression=Key('device_id').eq('m5stamp-s3-edge-01'),
                ScanIndexForward=False,
                Limit=limit
            )
            items = response.get('Items', [])
            if items:
                return items
        except Exception as e:
            print(f"[Error querying DynamoDB] {e}")

    # Live dynamic ticker: advance time if no real telemetry arrived in >3 seconds
    now = int(time.time())
    if simulated_history and (now - simulated_history[-1]["received_at"] >= 3):
        last = simulated_history[-1]
        is_alert = last.get("fire_alert", False)
        # Settle back to normal after 20 seconds of alert
        if is_alert and (now - last["received_at"] > 20):
            is_alert = False
            
        if is_alert:
            new_temp = round(last["temperature_c"] + random.uniform(-0.5, 0.5), 2)
            new_gas = round(last["gas_resistance_kohm"] + random.uniform(-0.2, 0.2), 2)
            act = "EMERGENCY_ALERT"
        else:
            new_temp = round(24.2 + random.uniform(-0.3, 0.3), 2)
            new_gas = round(44.5 + random.uniform(-0.6, 0.6), 2)
            act = "NORMAL_CYCLE"
            
        new_soc = round(max(5.0, last["battery_soc_pct"] - 0.01), 2)
        new_v = round(2.50 + (new_soc / 100.0) * 1.15, 3)
        simulated_history.append({
            "device_id": last.get("device_id", "m5stamp-s3-edge-01"),
            "received_at": now,
            "temperature_c": new_temp,
            "gas_resistance_kohm": new_gas,
            "battery_voltage": new_v,
            "battery_soc_pct": new_soc,
            "fire_alert": is_alert,
            "rl_action": act,
            "energy_mJ": 576.0 if act == "EMERGENCY_ALERT" else 1.2
        })
        if len(simulated_history) > 100:
            simulated_history.pop(0)

    return simulated_history[-limit:]

@app.post("/telemetry")
@app.post("/api/telemetry")
async def receive_telemetry(payload: dict):
    """Direct ingestion endpoint for ESP32-S3 (or Wokwi simulator) over HTTP."""
    if "received_at" not in payload:
        payload["received_at"] = int(time.time())
    if "energy_mJ" not in payload:
        act = payload.get("rl_action", "NORMAL_CYCLE")
        payload["energy_mJ"] = 576.0 if act == "EMERGENCY_ALERT" else (1.2 if act == "NORMAL_CYCLE" else 0.05)
    simulated_history.append(payload)
    if len(simulated_history) > 200:
        simulated_history.pop(0)
    print(f"[Telemetry Ingested] Device: {payload.get('device_id')} | Temp: {payload.get('temperature_c')} °C | Gas: {payload.get('gas_resistance_kohm')} kOhm | Action: {payload.get('rl_action')}")
    return {"status": "success", "received": payload}

@app.post("/api/simulate_spike")
def trigger_spike():
    """Trigger a fire spike immediately during a live demo."""
    last = simulated_history[-1]
    new_point = {
        "device_id": "m5stamp-s3-edge-01",
        "received_at": int(time.time()),
        "temperature_c": round(last["temperature_c"] + random.uniform(8.0, 15.0), 2),
        "gas_resistance_kohm": round(max(1.8, last["gas_resistance_kohm"] - 14.0), 2),
        "battery_voltage": 3.24,
        "battery_soc_pct": round(last["battery_soc_pct"] - 0.2, 1),
        "fire_alert": True,
        "rl_action": "EMERGENCY_ALERT",
        "energy_mJ": 576.0
    }
    simulated_history.append(new_point)
    return {"message": "Simulated fire/gas hazard injected!", "point": new_point}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
