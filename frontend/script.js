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

        loadVehiclePath(vehicleId);
        loadHealthTrend(vehicleId);

    } catch (error) {
        resultDiv.innerHTML = "Error fetching data.";
        console.error("Fetch error:", error);
    }
}


let map;
let polyline;
let marker;

async function loadVehiclePath(vehicleId) {

    const BASE_URL = window.location.hostname === "localhost"
        ? "http://127.0.0.1:8000"
        : "https://velos-production.up.railway.app";

    const response = await fetch(`${BASE_URL}/vehicle/${vehicleId}/path?limit=100`);
    const data = await response.json();

    if (!data.length) return;

    const coordinates = data.reverse().map(p => [p.latitude, p.longitude]);

    if (!map) {
        map = L.map('map').setView(coordinates[0], 13);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
    }

    if (polyline) polyline.remove();
    if (marker) marker.remove();

    polyline = L.polyline(coordinates, { color: 'blue' }).addTo(map);
    map.fitBounds(polyline.getBounds());

    const latest = coordinates[coordinates.length - 1];

    marker = L.marker(latest).addTo(map)
        .bindPopup("Current Vehicle Location")
        .openPopup();
}



let healthChart;

async function loadHealthTrend(vehicleId) {

    const BASE_URL = window.location.hostname === "localhost"
        ? "http://127.0.0.1:8000"
        : "https://velos-production.up.railway.app";

    const response = await fetch(`${BASE_URL}/vehicle/${vehicleId}/health-trend?limit=50`);
    const data = await response.json();

    const labels = data.map(p => new Date(p.timestamp).toLocaleTimeString());
    const healthData = data.map(p => p.health_score);

    const ctx = document.getElementById('healthChart').getContext('2d');

    if (healthChart) {
        healthChart.destroy();
    }

    healthChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Health Score',
                data: healthData,
                borderColor: 'lime',
                fill: false,
                tension: 0.3
            }]
        },
        options: {
            scales: {
                y: {
                    min: 0,
                    max: 100
                }
            }
        }
    });
}

async function projectLife() {

    const vehicleId = document.getElementById("vehicleInput").value;
    const years = document.getElementById("yearsInput").value || 0;
    const months = document.getElementById("monthsInput").value || 0;
    const hours = document.getElementById("hoursInput").value || 0;

    const BASE_URL = window.location.hostname === "localhost"
        ? "http://127.0.0.1:8000"
        : "https://velos-production.up.railway.app";

    const response = await fetch(
        `${BASE_URL}/vehicle/${vehicleId}/project-life?years=${years}&months=${months}&hours=${hours}`
    );

    const data = await response.json();

    document.getElementById("projectionResult").innerHTML =
        `Projected Health: ${data.projected_health_percentage}% <br>
         Life Remaining: ${data.projected_life_remaining_years} years`;
}