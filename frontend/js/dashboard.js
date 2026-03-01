requireAuth();

document.addEventListener("DOMContentLoaded", () => {
    loadOverview();
    loadRiskDistribution();
    loadVehiclesTable();
});

/* =========================
   Helper: Format Years
========================= */
function formatYearsToReadable(yearsDecimal) {
    if (!yearsDecimal && yearsDecimal !== 0) return "--";

    const years = Math.floor(yearsDecimal);
    const months = Math.round((yearsDecimal - years) * 12);

    return `${years} yrs ${months} months`;
}

/* =========================
   Overview Cards
========================= */
async function loadOverview() {
    const response = await authFetch(`${BASE_URL}/fleet/summary`);
    if (!response.ok) return;

    const data = await response.json();

    document.getElementById("totalVehicles").innerText =
        data.fleet_size ?? "--";

    document.getElementById("averageHealth").innerText =
        data.average_health !== undefined
            ? data.average_health.toFixed(1) + "%"
            : "--";

    // summary endpoint does not return cost
    document.getElementById("totalCost").innerText = "--";
}
/* =========================
   Risk Distribution Chart
========================= */
async function loadRiskDistribution() {
    const response = await authFetch(`${BASE_URL}/fleet/risk-distribution`);
    if (!response.ok) return;

    const data = await response.json();

    const low = data.low_risk || 0;
    const moderate = data.moderate_risk || 0;
    const high = data.high_risk || 0;
    const critical = data.critical_risk || 0;

    const ctx = document.getElementById("riskChart").getContext("2d");

    if (window.riskChartInstance) {
        window.riskChartInstance.destroy();
    }

    window.riskChartInstance = new Chart(ctx, {
        type: "pie",
        data: {
            labels: ["Low", "Moderate", "High", "Critical"],
            datasets: [{
                data: [low, moderate, high, critical],
                backgroundColor: [
                    "#3b82f6",
                    "#f43f5e",
                    "#fb923c",
                    "#facc15"
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

async function loadVehiclesTable() {

    const vehiclesRes = await authFetch(`${BASE_URL}/vehicles`);
    if (!vehiclesRes.ok) return;

    const vehicles = await vehiclesRes.json();
    const tbody = document.querySelector("#rankingTable tbody");
    tbody.innerHTML = "";

    let enrichedVehicles = [];

    for (let vehicle of vehicles) {

        const healthRes = await authFetch(`${BASE_URL}/vehicle/${vehicle.number_plate}/health`);
        if (!healthRes.ok) continue;

        const health = await healthRes.json();

        enrichedVehicles.push({
            ...vehicle,
            health_score: health.health_score,
            predicted_life_years: health.predicted_life_years,
            risk_level: health.risk_level
        });
    }

    if (enrichedVehicles.length === 0) return;

    // Sort by health ascending
    enrichedVehicles.sort((a, b) => a.health_score - b.health_score);

    // Best & Worst cards
    const worst = enrichedVehicles[0];
    const best = enrichedVehicles[enrichedVehicles.length - 1];

    document.getElementById("worstVehicle").innerText =
        `${worst.name} (${worst.health_score.toFixed(1)}%)`;

    document.getElementById("bestVehicle").innerText =
        `${best.name} (${best.health_score.toFixed(1)}%)`;

    currentVehiclesData = enrichedVehicles;

    renderVehicles(currentVehiclesData);

    createRankingChart(enrichedVehicles);
}

/* =========================
   Navigation
========================= */
function openVehicle(vehicleId) {
    window.location.href = `vehicle.html?id=${vehicleId}`;
}

let viewMap;
let viewPolyline;
let viewMarker;

async function openVehicleView(vehicleId) {

    document.getElementById("vehicleViewCard").style.display = "block";

    /* Load vehicle details */
    const vehiclesRes = await authFetch(`${BASE_URL}/vehicles`);
    const vehicles = await vehiclesRes.json();
    const vehicle = vehicles.find(v => v.number_plate === vehicleId);
    if (!vehicle) return;

    document.getElementById("viewVehicleTitle").innerText =
        `${vehicle.name} ${vehicle.model} (${vehicle.number_plate})`;

    /* Load health */
    const healthRes = await authFetch(`${BASE_URL}/vehicle/${vehicleId}/health`);
    if (healthRes.ok) {
        const healthData = await healthRes.json();
        document.getElementById("viewHealthInfo").innerHTML =
            `Health Score: ${healthData.health_score}% | 
             Risk: ${healthData.risk_level}`;
    }

    /* Load latest telemetry */
    const telemetryRes = await authFetch(`${BASE_URL}/telemetry/${vehicleId}?limit=1`);
    if (telemetryRes.ok) {
        const data = await telemetryRes.json();
        if (data.length > 0) {
            const t = data[0];
            document.getElementById("viewTelemetry").innerHTML = `
                <p>Speed: ${t.speed} km/h</p>
                <p>Engine Temp: ${t.engine_temp} °C</p>
                <p>RPM: ${t.rpm}</p>
                <p>Battery: ${t.battery_level}</p>
                <p>Tire Pressure: ${t.tire_pressure}</p>
            `;
        }
    }

    /* Load path map */
    const pathRes = await authFetch(`${BASE_URL}/vehicle/${vehicleId}/path?limit=50`);
    if (pathRes.ok) {
        const pathData = await pathRes.json();
        if (!pathData.length) return;

        const coords = pathData.map(p => [p.latitude, p.longitude]);

        if (!viewMap) {
            viewMap = L.map('viewMap').setView(coords[0], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(viewMap);
        }

        if (viewPolyline) viewPolyline.remove();
        if (viewMarker) viewMarker.remove();

        viewPolyline = L.polyline(coords, { color: '#00ff88' }).addTo(viewMap);
        viewMap.fitBounds(viewPolyline.getBounds());

        viewMarker = L.marker(coords[coords.length - 1]).addTo(viewMap);
    }
}

function closeVehicleView() {
    document.getElementById("vehicleViewCard").style.display = "none";
}


function createRankingChart(data) {

    const ctx = document.getElementById("rankingChart").getContext("2d");

    const worstFive = data.slice(0, 5);

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: worstFive.map(v => v.number_plate),
            datasets: [{
                label: "Health Score",
                data: worstFive.map(v => v.health_score)
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

let currentVehiclesData = [];


function applySort() {

    const type = document.getElementById("sortSelect").value;

    if (type === "health") {
        currentVehiclesData.sort((a,b)=>a.health_score - b.health_score);
    }

    if (type === "year") {
        currentVehiclesData.sort((a,b)=>b.year - a.year);
    }

    if (type === "risk") {
        const order = { Critical:1, High:2, Moderate:3, Low:4 };
        currentVehiclesData.sort((a,b)=>order[a.risk_level] - order[b.risk_level]);
    }

    renderVehicles(currentVehiclesData);
}

function renderVehicles(data) {

    const tbody = document.querySelector("#rankingTable tbody");
    tbody.innerHTML = "";

    data.forEach(vehicle => {

        const riskClass = `risk-${vehicle.risk_level.toLowerCase()}`;

        tbody.innerHTML += `
            <tr class="clickable-row" onclick="openVehicleView('${vehicle.number_plate}')">
                <td>
                    <div style="font-weight:600">${vehicle.name} ${vehicle.model}</div>
                    <div style="font-size:12px;color:#aaa">
                        ${vehicle.number_plate}
                    </div>
                </td>
                <td>${vehicle.model}</td>
                <td>${vehicle.year}</td>
                <td>
                    <div class="health-bar">
                        <div class="health-fill" style="width:${vehicle.health_score}%"></div>
                    </div>
                    <div class="health-text">${vehicle.health_score.toFixed(1)}%</div>
                </td>
                <td>${formatYearsToReadable(vehicle.predicted_life_years)}</td>
                <td>
                    <span class="risk-badge ${riskClass}">
                        ${vehicle.risk_level}
                    </span>
                </td>
            </tr>
        `;
    });
}

function goToCreateVehicle() {
    window.location.href = "create-vehicle.html";
}