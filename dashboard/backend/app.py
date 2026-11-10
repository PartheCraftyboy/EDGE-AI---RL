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

    # Return simulated realistic history
    return simulated_history[-limit:]

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
