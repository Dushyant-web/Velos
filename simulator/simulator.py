import requests
import random
import time
import os

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

vehicles = [f"DL01AB{1000+i}" for i in range(200)]

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

try:
    while True:
        for v in vehicles:
            state = vehicle_state[v]

            state["speed"] = max(0, min(state["speed"] + random.randint(-5, 5), 140))
            state["rpm"] = state["speed"] * 40
            state["engine_temp"] += random.uniform(-1, 1.5)
            state["fuel"] -= random.uniform(0.05, 0.2)
            state["battery_level"] -= random.uniform(0.01, 0.05)
            state["latitude"] += random.uniform(-0.0005, 0.0005)
            state["longitude"] += random.uniform(-0.0005, 0.0005)
            state["tire_pressure"] += random.uniform(-0.1, 0.1)

            payload = {
                "vehicle_id": v,
                **state
            }

            response = requests.post(f"{BASE_URL}/telemetry", json=payload)

        print("Batch sent successfully")
        time.sleep(3)

except KeyboardInterrupt:
    print("\n🛑 Simulation stopped cleanly.")