requireAuth();

function formatYearsToReadable(yearsDecimal) {
    if (!yearsDecimal && yearsDecimal !== 0) return "--";
    const years = Math.floor(yearsDecimal);
    const months = Math.round((yearsDecimal - years) * 12);
    return `${years} yrs ${months} months`;
}

let allVehicles = [];

document.addEventListener("DOMContentLoaded", () => {
    loadVehicles();
});

async function loadVehicles() {

    const vehiclesRes = await authFetch(`${BASE_URL}/vehicles`);
    if (!vehiclesRes.ok) return;

    const vehicles = await vehiclesRes.json();
    let enriched = [];

    for (let vehicle of vehicles) {

        const healthRes = await authFetch(`${BASE_URL}/vehicle/${vehicle.number_plate}/health`);
        if (!healthRes.ok) continue;

        const health = await healthRes.json();

        const failureRes = await authFetch(`${BASE_URL}/vehicle/${vehicle.number_plate}/failure-probability`);
        const alertsRes = await authFetch(`${BASE_URL}/alerts/${vehicle.number_plate}`);

        let failureProbability = null;
        if (failureRes.ok) {
            const fail = await failureRes.json();
            failureProbability = fail.engine_failure_probability_90_days * 100;
        }

        let alertCount = 0;
        if (alertsRes.ok) {
            const alerts = await alertsRes.json();
            alertCount = alerts.length;
        }

        enriched.push({
            ...vehicle,
            health_score: health.health_score,
            risk_level: health.risk_level,
            predicted_life_years: health.predicted_life_years,
            failure_probability: failureProbability,
            alerts_count: alertCount
        });
    }

    allVehicles = enriched;
    renderVehicles(allVehicles);
}

function renderVehicles(data) {

    const tbody = document.querySelector("#vehiclesTable tbody");
    tbody.innerHTML = "";

    data.forEach(vehicle => {

        const riskClass = `risk-${vehicle.risk_level.toLowerCase()}`;

        tbody.innerHTML += `
            <!-- MAIN ROW -->
            <tr onclick="toggleDetails('${vehicle.number_plate}')">

                <td>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        
                        <div>
                            <div style="font-weight:600">
                                ${vehicle.name} ${vehicle.model}
                            </div>
                            <div style="font-size:12px;color:#aaa">
                                ${vehicle.number_plate}
                            </div>
                        </div>

                        <button 
                            class="view-intel-btn"
                            onclick="event.stopPropagation(); window.location.href='vehicle-intelligence.html?id=${vehicle.number_plate}'">
                            View Intelligence
                        </button>

                    </div>
                </td>

                <td>${vehicle.year}</td>
                <td>${vehicle.health_score.toFixed(1)}%</td>

                <td>
                    <span class="risk-badge ${riskClass}">
                        ${vehicle.risk_level}
                    </span>
                </td>

                <td>${formatYearsToReadable(vehicle.predicted_life_years)}</td>
            </tr>

            <!-- EXPANDABLE DETAILS ROW -->
            <tr id="details-${vehicle.number_plate}" class="details-row" style="display:none;">
                <td colspan="5">
                    <div class="details-card">

                        <!-- TOP SECTION -->
                        <div class="top-section">

                            <!-- PROJECTION SIMULATOR -->
                            <div class="projection-info">
                                <h3>Health Projection Simulator</h3>
                                <p>
                                    Enter how long the vehicle will continue operating.
                                    The system estimates future health and failure timeline.
                                </p>

                                <div class="projection-controls">

                                    <div class="input-group">
                                        <label>Years</label>
                                        <input type="number" id="years-${vehicle.number_plate}" value="1" min="0">
                                    </div>

                                    <div class="input-group">
                                        <label>Months</label>
                                        <input type="number" id="months-${vehicle.number_plate}" value="0" min="0">
                                    </div>

                                    <div class="input-group">
                                        <label>Hours</label>
                                        <input type="number" id="hours-${vehicle.number_plate}" value="0" min="0">
                                    </div>

                                    <button class="project-btn"
                                        onclick="runProjection('${vehicle.number_plate}', ${vehicle.health_score})">
                                        Run Projection
                                    </button>

                                </div>
                            </div>

                            <!-- RISK STATS -->
                            <div class="stats-column">

                                <div class="stat-card">
                                    <div class="stat-title">Failure Probability (90d)</div>
                                    <div class="stat-value ${getFailureClass(vehicle.failure_probability)}">
                                        ${vehicle.failure_probability
                                            ? vehicle.failure_probability.toFixed(1) + "%"
                                            : "--"}
                                    </div>
                                    <div class="progress-bar">
                                        <div class="progress-fill ${getFailureClass(vehicle.failure_probability)}"
                                             style="width:${vehicle.failure_probability || 0}%">
                                        </div>
                                    </div>
                                </div>

                                <div class="stat-card">
                                    <div class="stat-title">Active Alerts</div>
                                    <div class="stat-value ${getAlertClass(vehicle.alerts_count)}">
                                        ${vehicle.alerts_count}
                                    </div>
                                </div>

                            </div>

                        </div>

                        <!-- PROJECTION RESULT -->
                        <div id="projection-result-${vehicle.number_plate}" class="projection-summary"></div>

                        <!-- GRAPH -->
                        <div class="chart-fullwidth">
                            <canvas id="projection-chart-${vehicle.number_plate}"></canvas>
                        </div>

                    </div>
                </td>
            </tr>
        `;
    });
}

function toggleDetails(plate) {
    const row = document.getElementById(`details-${plate}`);
    if (!row) return;

    row.style.display =
        row.style.display === "none" ? "table-row" : "none";
}

async function runProjection(plate, currentHealth) {

    const years = document.getElementById(`years-${plate}`).value || 0;
    const months = document.getElementById(`months-${plate}`).value || 0;
    const hours = document.getElementById(`hours-${plate}`).value || 0;

    const res = await authFetch(
        `${BASE_URL}/vehicle/${plate}/project-life?years=${years}&months=${months}&hours=${hours}`
    );

    if (!res.ok) return;

    const data = await res.json();

    document.getElementById(`projection-result-${plate}`).innerHTML = `
        <strong>Projected Health:</strong> ${data.projected_health_percentage.toFixed(1)}% <br>
        <strong>Life Remaining:</strong> ${data.projected_life_remaining_years.toFixed(2)} years <br>
        <strong>Estimated Failure Date:</strong> ${data.predicted_failure_date}
    `;

    renderProjectionChart(plate, currentHealth, data.projected_health_percentage);
}

function renderProjectionChart(plate, currentHealth, projectedHealth) {

    const canvas = document.getElementById(`projection-chart-${plate}`);
    const ctx = canvas.getContext("2d");

    if (window[`chart-${plate}`]) {
        window[`chart-${plate}`].destroy();
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, "rgba(0,255,136,0.4)");
    gradient.addColorStop(1, "rgba(0,255,136,0.05)");

    window[`chart-${plate}`] = new Chart(ctx, {
        type: "line",
        data: {
            labels: ["Now", "Projected"],
            datasets: [{
                label: "Health Projection",
                data: [currentHealth, projectedHealth],
                fill: true,
                backgroundColor: gradient,
                borderColor: "#00ff88",
                borderWidth: 2,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 800 },
            scales: {
                y: { min: 0, max: 100 }
            }
        }
    });
}

function getFailureClass(value) {
    if (!value) return "stat-safe";
    if (value < 10) return "stat-safe";
    if (value < 30) return "stat-warning";
    return "stat-danger";
}

function getAlertClass(value) {
    if (!value) return "stat-safe";
    if (value < 3) return "stat-warning";
    return "stat-danger";
}