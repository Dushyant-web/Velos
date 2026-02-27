async function getTelemetry() {
    const vehicleId = document.getElementById("vehicleInput").value;
    const resultDiv = document.getElementById("result");

    if (!vehicleId) {
        resultDiv.innerHTML = "Please enter a number plate.";
        return;
    }

    // Dynamic backend URL (NO trailing slash)
    const BASE_URL = window.location.hostname === "localhost"
        ? "http://127.0.0.1:8000"
        : "https://velos-production.up.railway.app";

    try {
        const response = await fetch(`${BASE_URL}/telemetry/${vehicleId}?limit=1`);

        if (!response.ok) {
            throw new Error("Server error");
        }

        const data = await response.json();

        if (!data || data.length === 0) {
            resultDiv.innerHTML = "No data found.";
            return;
        }

        const vehicle = data[0];

        resultDiv.innerHTML = `
            <h3>Latest Telemetry</h3>
            <p><b>Speed:</b> ${vehicle.speed} km/h</p>
            <p><b>Engine Temp:</b> ${vehicle.engine_temp} °C</p>
            <p><b>Fuel:</b> ${vehicle.fuel}</p>
            <p><b>RPM:</b> ${vehicle.rpm}</p>
            <p><b>Battery:</b> ${vehicle.battery_level}</p>
            <p><b>Location:</b> ${vehicle.latitude}, ${vehicle.longitude}</p>
            <p><b>Tire Pressure:</b> ${vehicle.tire_pressure}</p>
            <p><b>Timestamp:</b> ${vehicle.timestamp}</p>
        `;

    } catch (error) {
        resultDiv.innerHTML = "Error fetching data.";
        console.error("Fetch error:", error);
    }
}