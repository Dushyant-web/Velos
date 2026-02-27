import requests
import random
import time
import os

# Works locally AND in production
BASE_URL = "https://velos-production.up.railway.app"

# 200 vehicles
vehicles = [f"DL01AB{1000+i}" for i in range(20)]

# Initial state
vehicle_state = {}

for v in vehicles:
    vehicle_state[v] = {
        "speed": random.randint(40, 80),
        "engine_temp": 85.0,
        "battery_level": 100.0,
        "fuel": 50.0,
        "rpm": 2500,
        "latitude": 28.6139,
        "longitude": 77.2090,
        "tire_pressure": 32.0
    }

print("🚗 Starting 20 vehicle simulation...\n")
print(f"📡 Sending data to: {BASE_URL}\n")

try:
    while True:
        for v in vehicles:
            state = vehicle_state[v]

            # Simulate movement + variation
            state["speed"] = max(0, min(state["speed"] + random.randint(-5, 5), 140))
            state["rpm"] = state["speed"] * 40
            state["engine_temp"] += random.uniform(-1, 1.5)
            state["fuel"] = max(0, state["fuel"] - random.uniform(0.05, 0.2))
            state["battery_level"] = max(0, state["battery_level"] - random.uniform(0.01, 0.05))
            state["latitude"] += random.uniform(-0.0005, 0.0005)
            state["longitude"] += random.uniform(-0.0005, 0.0005)
            state["tire_pressure"] += random.uniform(-0.1, 0.1)

            payload = {
                "vehicle_id": v,
                **state
            }

            try:
                response = requests.post(f"{BASE_URL}/telemetry", json=payload)

                if response.status_code != 200:
                    print(f"❌ Error {v}: {response.status_code} - {response.text}")

            except Exception as e:
                print(f"🚨 Request failed for {v}: {e}")

        print("✅ Batch sent successfully\n")
        time.sleep(3)

except KeyboardInterrupt:
    print("\n🛑 Simulation stopped cleanly.")