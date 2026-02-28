import requests
import random
import time

BASE_URL = "https://velos-production.up.railway.app"

vehicles = [f"DL01AB{1000+i}" for i in range(20)]

vehicle_state = {}

for v in vehicles:
    vehicle_state[v] = {
        "speed": random.randint(40, 80),
        "engine_temp": random.uniform(85, 95),
        "battery_level": 100.0,
        "fuel": 60.0,
        "rpm": 2500,
        "latitude": 28.6139,
        "longitude": 77.2090,
        "tire_pressure": 32.0
    }

print("🚗 Starting 20 vehicle simulation...\n")
print(f"📡 Sending data to: {BASE_URL}\n")


def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))


try:
    while True:
        for v in vehicles:
            state = vehicle_state[v]

            # --- SPEED ---
            state["speed"] += random.randint(-5, 5)
            state["speed"] = clamp(state["speed"], 0, 140)

            # --- RPM (linked to speed) ---
            state["rpm"] = clamp(state["speed"] * random.uniform(30, 45), 800, 4500)

            # --- ENGINE TEMP ---
            # heats when speed high, cools when low
            if state["speed"] > 80:
                state["engine_temp"] += random.uniform(0.2, 0.8)
            else:
                state["engine_temp"] -= random.uniform(0.1, 0.5)

            # occasional rare overheating event
            if random.random() < 0.02:
                state["engine_temp"] += random.uniform(5, 15)

            state["engine_temp"] = clamp(state["engine_temp"], 75, 120)

            # --- FUEL ---
            state["fuel"] -= random.uniform(0.02, 0.1)

            # refuel when empty
            if state["fuel"] <= 5:
                state["fuel"] = 60.0

            state["fuel"] = clamp(state["fuel"], 0, 100)

            # --- BATTERY ---
            state["battery_level"] -= random.uniform(0.005, 0.02)

            if state["battery_level"] < 40:
                state["battery_level"] += random.uniform(1, 3)

            state["battery_level"] = clamp(state["battery_level"], 40, 100)

            # --- GPS MOVEMENT ---
            state["latitude"] += random.uniform(-0.0005, 0.0005)
            state["longitude"] += random.uniform(-0.0005, 0.0005)

            # --- TIRE PRESSURE ---
            state["tire_pressure"] += random.uniform(-0.05, 0.05)
            state["tire_pressure"] = clamp(state["tire_pressure"], 30, 35)

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