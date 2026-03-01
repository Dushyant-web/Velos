import requests
import random
import time

BASE_URL = "https://velos-production.up.railway.app"

# 🔐 Your credentials (CHANGE THESE)
EMAIL = "jarvis.projects.notifications@gmail.com"
PASSWORD = "TestPass"


def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))


# 🔐 LOGIN FUNCTION
def login():
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": EMAIL,   # OAuth2 requires 'username'
                "password": PASSWORD
            }
        )

        if response.status_code != 200:
            print("❌ Login failed:", response.text)
            return None

        token = response.json()["access_token"]
        print("🔐 Logged in successfully\n")
        return token

    except Exception as e:
        print("🚨 Login error:", e)
        return None


# 🔥 Fetch vehicles securely
def fetch_registered_vehicles(headers):
    try:
        response = requests.get(
            f"{BASE_URL}/vehicles",
            headers=headers
        )

        if response.status_code != 200:
            print("❌ Failed to fetch vehicles:", response.text)
            return []

        data = response.json()
        return [v["number_plate"] for v in data]

    except Exception as e:
        print("🚨 Error fetching vehicles:", e)
        return []


# --- LOGIN FIRST ---
token = login()

if not token:
    exit()

HEADERS = {
    "Authorization": f"Bearer {token}"
}

# --- Get vehicles from DB ---
vehicles = fetch_registered_vehicles(HEADERS)

if not vehicles:
    print("⚠️ No vehicles registered. Simulation stopped.")
    exit()

print(f"🚗 Starting simulation for {len(vehicles)} vehicles...\n")
print(f"📡 Sending data to: {BASE_URL}\n")

# Initialize state per vehicle
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

try:
    while True:

        vehicles = fetch_registered_vehicles(HEADERS)

        for v in vehicles:

            if v not in vehicle_state:
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

            state = vehicle_state[v]

            # SPEED
            state["speed"] += random.randint(-5, 5)
            state["speed"] = clamp(state["speed"], 0, 140)

            # RPM
            state["rpm"] = clamp(state["speed"] * random.uniform(30, 45), 800, 4500)

            # ENGINE TEMP
            if state["speed"] > 80:
                state["engine_temp"] += random.uniform(0.2, 0.8)
            else:
                state["engine_temp"] -= random.uniform(0.1, 0.5)

            if random.random() < 0.02:
                state["engine_temp"] += random.uniform(5, 15)

            state["engine_temp"] = clamp(state["engine_temp"], 75, 120)

            # FUEL
            state["fuel"] -= random.uniform(0.02, 0.1)
            if state["fuel"] <= 5:
                state["fuel"] = 60.0
            state["fuel"] = clamp(state["fuel"], 0, 100)

            # BATTERY
            state["battery_level"] -= random.uniform(0.005, 0.02)
            if state["battery_level"] < 40:
                state["battery_level"] += random.uniform(1, 3)
            state["battery_level"] = clamp(state["battery_level"], 40, 100)

            # GPS
            state["latitude"] += random.uniform(-0.0005, 0.0005)
            state["longitude"] += random.uniform(-0.0005, 0.0005)

            # TIRE PRESSURE
            state["tire_pressure"] += random.uniform(-0.05, 0.05)
            state["tire_pressure"] = clamp(state["tire_pressure"], 30, 35)

            payload = {
                "vehicle_id": v,
                **state
            }

            try:
                response = requests.post(
                    f"{BASE_URL}/telemetry",
                    json=payload,
                    headers=HEADERS
                )

                if response.status_code != 200:
                    print(f"❌ Error {v}: {response.status_code} - {response.text}")

                time.sleep(0.05)

            except Exception as e:
                print(f"🚨 Request failed for {v}: {e}")

        print("✅ Batch sent successfully\n")
        time.sleep(3)

except KeyboardInterrupt:
    print("\n🛑 Simulation stopped cleanly.")