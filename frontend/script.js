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
        datasets: [
            {
                label: 'Historical Health',
                data: healthData,
                borderColor: '#00ff88',
                backgroundColor: 'rgba(0,255,136,0.15)',
                fill: true,
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 0
            },
            {
                label: 'Projected Health',
                data: [],
                borderColor: '#ffaa00',
                borderDash: [8, 6],
                fill: false,
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 0
            }
        ]
    },
    options: {
        responsive: true,
        animation: {
            duration: 1000,
            easing: 'easeOutQuart'
        },
        interaction: {
            mode: 'index',
            intersect: false
        },
        plugins: {
            legend: {
                labels: {
                    color: '#aaa'
                }
            },
            tooltip: {
                backgroundColor: '#111',
                borderColor: '#00ff88',
                borderWidth: 1,
                titleColor: '#00ff88',
                bodyColor: '#fff',
                callbacks: {
                    label: function(context) {
                        return `Health: ${context.raw.toFixed(2)}%`;
                    }
                }
            },
            annotation: {
                annotations: {
                    dangerZone: {
                        type: 'box',
                        yMin: 0,
                        yMax: 30,
                        backgroundColor: 'rgba(255,0,0,0.05)'
                    },
                }     
            }
        },
        scales: {
            x: {
                ticks: {
                    color: '#666'
                },
                grid: {
                    color: 'rgba(255,255,255,0.04)'
                }
            },
            y: {
                min: 0,
                max: 100,
                ticks: {
                    color: '#666'
                },
                grid: {
                    color: 'rgba(255,255,255,0.04)'
                }
            }
        }
    }
});
}

async function projectLife() {

    const vehicleId = document.getElementById("vehicleInput").value;
    const years = parseFloat(document.getElementById("yearsInput").value) || 0;
    const months = parseFloat(document.getElementById("monthsInput").value) || 0;
    const hours = parseFloat(document.getElementById("hoursInput").value) || 0;

    if (years === 0 && months === 0 && hours === 0) return;

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

    if (!healthChart) return;

    // 🔥 RESET OLD PROJECTION FIRST
    const historicalLength = healthChart.data.datasets[0].data.length;
    
    // Remove future labels
    healthChart.data.labels = healthChart.data.labels.slice(0, historicalLength);
    
    // Clear projected dataset
    healthChart.data.datasets[1].data = [];
    
    // Keep dangerZone but remove todayLine if exists
    if (healthChart.options.plugins.annotation.annotations.todayLine) {
        delete healthChart.options.plugins.annotation.annotations.todayLine;
    }
    
    healthChart.update();

    const totalYears = years + (months / 12) + (hours / (24 * 365));
    const totalLife = 20;
    const steps = Math.ceil(totalYears * 12);

    const projectedFinalLife = data.projected_life_remaining_years;
    const currentHealth = healthChart.data.datasets[0].data.slice(-1)[0];
    const currentLifeYears = (currentHealth / 100) * totalLife;

    const monthlyDecay = (currentLifeYears - projectedFinalLife) / steps;

    let todayIndex = healthChart.data.labels.length - 1;

    let projectedLabels = [];
    let projectedData = [];

    let life = currentLifeYears;
    let futureDate = new Date();

    for (let i = 1; i <= steps; i++) {
        futureDate.setMonth(futureDate.getMonth() + 1);

        life -= monthlyDecay;
        if (life < 0) life = 0;

        projectedLabels.push(futureDate.toLocaleDateString());
        projectedData.push((life / totalLife) * 100);
    }

    // Extend labels
    healthChart.data.labels = [
        ...healthChart.data.labels,
        ...projectedLabels
    ];

    // Update projected dataset only
    healthChart.data.datasets[1].data = [
        ...Array(todayIndex + 1).fill(null),
        ...projectedData
    ];

    // Add vertical “Today” marker
    healthChart.options.plugins.annotation.annotations = {
        todayLine: {
            type: 'line',
            xMin: healthChart.data.labels[todayIndex],
            xMax: healthChart.data.labels[todayIndex],
            borderColor: 'red',
            borderWidth: 2,
            label: {
                content: 'Today',
                enabled: true,
                position: 'start'
            }
        }
    };

    healthChart.update();
}