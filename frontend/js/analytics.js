requireAuth();

let healthChart;
let riskChart;
let costChart;
let currentRange = 30;

// ===============================
// Init
// ===============================
document.addEventListener("DOMContentLoaded", () => {
    loadFleetOverview();
    loadFleetRiskDistribution();
    loadFleetRanking();
});

// ===============================
// Range Filter
// ===============================
function setRange(days) {
    currentRange = days;
    loadFleetRanking();
}

// ===============================
// Fleet Overview Cards + Glow
// ===============================
async function loadFleetOverview() {
    const res = await authFetch(`${BASE_URL}/fleet/summary`);
    if (!res.ok) return;

    const data = await res.json();

    const avgHealth = (data.average_health ?? 0);
    document.getElementById("fleetAvgHealth").innerText = avgHealth.toFixed(1) + "%";
}

function applyKpiGlow(avgHealth, highRisk) {
    const healthCard = document.getElementById("fleetAvgHealth").parentElement;
    const riskCard = document.getElementById("fleetHighRisk").parentElement;

    healthCard.classList.remove("kpi-good", "kpi-warning", "kpi-danger");
    riskCard.classList.remove("kpi-good", "kpi-warning", "kpi-danger");

    if (avgHealth >= 75) healthCard.classList.add("kpi-good");
    else if (avgHealth >= 50) healthCard.classList.add("kpi-warning");
    else healthCard.classList.add("kpi-danger");

    if (highRisk === 0) riskCard.classList.add("kpi-good");
    else if (highRisk <= 3) riskCard.classList.add("kpi-warning");
    else riskCard.classList.add("kpi-danger");
}

// ===============================
// Risk Distribution Chart
// ===============================
async function loadFleetRiskDistribution() {
    const res = await authFetch(`${BASE_URL}/fleet/risk-distribution`);
    if (!res.ok) return;

    const data = await res.json();
    const ctx = document.getElementById("fleetRiskChart").getContext("2d");

    if (riskChart) riskChart.destroy();

    riskChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: ["Low", "Moderate", "High", "Critical"],
            datasets: [{
                data: [
                    data.low_risk,
                    data.moderate_risk,
                    data.high_risk,
                    data.critical_risk
                ],
                backgroundColor: [
                    "rgba(0,255,136,0.6)",
                    "rgba(255,215,0,0.6)",
                    "rgba(255,140,0,0.6)",
                    "rgba(255,0,0,0.6)"
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 800, easing: 'easeOutQuart' },
            plugins: {
                legend: { labels: { color: "#ccc" } }
            }
        }
    });
}

// ===============================
// Fleet Ranking + Heatmap + Volatility
// ===============================
async function loadFleetRanking() {
    const res = await authFetch(`${BASE_URL}/fleet/ranking?days=${currentRange}`);
    if (!res.ok) return;

    const responseData = await res.json();
    const data = responseData.fleet_ranking_worst_to_best || [];

    // Calculate high risk count dynamically
    const highRiskCount = data.filter(v =>
        v.risk_level === "High" || v.risk_level === "Critical"
    ).length;

    document.getElementById("fleetHighRisk").innerText = highRiskCount;

    // Fleet Risk Exposure Index (proxy metric)
    const exposureScore = highRiskCount * 100;
    const exposureEl = document.getElementById("fleetTotalCost");
    if (exposureEl) {
        exposureEl.innerText = exposureScore;
    }

    // Apply glow after real risk is calculated
    const avgHealth = data.length
        ? data.reduce((sum, v) => sum + v.health_score, 0) / data.length
        : 0;

    applyKpiGlow(avgHealth, highRiskCount);

    const labels = data.map(v => v.vehicle_id);
    const healthScores = data.map(v => v.health_score);
    const costForecast = data.map(v => v.predicted_life_years || 0);

    renderHealthComparison(labels, healthScores);
    renderCostForecast(labels, costForecast);
    renderRiskHeatmap(data);
    calculateVolatility(healthScores);
}

function calculateVolatility(values) {
    if (!values.length) return;

    const avg = values.reduce((a,b)=>a+b,0) / values.length;
    const variance = values.reduce((sum,v)=> sum + Math.pow(v-avg,2),0) / values.length;
    const volatility = Math.sqrt(variance);

    const volatilityEl = document.getElementById("fleetVolatility");
    volatilityEl.innerText = volatility.toFixed(2);

    let explanation = "";

    if (volatility < 5)
        explanation = "Stable fleet – vehicle health levels are consistent.";
    else if (volatility < 15)
        explanation = "Moderate variation – some vehicles require attention.";
    else
        explanation = "High instability – fleet health is uneven and risky.";

    let helper = document.getElementById("volatilityHelperText");
    if (!helper) {
        helper = document.createElement("div");
        helper.id = "volatilityHelperText";
        helper.style.marginTop = "6px";
        helper.style.fontSize = "12px";
        helper.style.color = "#aaa";
        volatilityEl.parentElement.appendChild(helper);
    }

    helper.innerText = explanation;
}

function renderRiskHeatmap(data) {
    const container = document.getElementById("riskHeatmap");
    container.innerHTML = "";

    if (!data.length) {
        container.innerHTML = "<div style='color:#888'>No fleet data available</div>";
        return;
    }

    // Make grid layout consistent with dashboard cards
    container.style.display = "grid";
    container.style.gridTemplateColumns = "repeat(auto-fit, minmax(160px, 1fr))";
    container.style.gap = "16px";

    data.forEach(vehicle => {
        const card = document.createElement("div");
        card.className = "heatmap-card";
        card.style.background = "#111";
        card.style.padding = "16px";
        card.style.borderRadius = "12px";
        card.style.border = "1px solid rgba(255,255,255,0.05)";
        card.style.transition = "0.3s ease";

        const risk = vehicle.risk_level.toLowerCase();

        let glowColor = "#00ff88";
        if (risk === "moderate") glowColor = "#ffd700";
        if (risk === "high") glowColor = "#ff8c00";
        if (risk === "critical") glowColor = "#ff0000";

        card.style.boxShadow = `0 0 15px ${glowColor}20`;

        card.innerHTML = `
            <div style="font-size:12px;color:#aaa;margin-bottom:6px">
                ${vehicle.vehicle_id}
            </div>
            <div style="font-size:26px;font-weight:700;margin-bottom:6px">
                ${vehicle.health_score.toFixed(0)}%
            </div>
            <div style="font-size:13px;color:${glowColor};font-weight:600">
                ${vehicle.risk_level}
            </div>
        `;

        container.appendChild(card);
    });

    let heatNote = document.getElementById("heatmapNote");
    if (!heatNote) {
        heatNote = document.createElement("div");
        heatNote.id = "heatmapNote";
        heatNote.style.marginTop = "12px";
        heatNote.style.fontSize = "12px";
        heatNote.style.color = "#aaa";
        container.parentElement.appendChild(heatNote);
    }

    heatNote.innerText =
        "Each card represents a vehicle's current risk state. Green = stable, Yellow = moderate attention, Orange = high concern, Red = critical.";
}

// ===============================
// Health Comparison Chart
// ===============================
function renderHealthComparison(labels, values) {
    const ctx = document.getElementById("fleetHealthChart").getContext("2d");

    if (healthChart) healthChart.destroy();

    healthChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Health Score (%)",
                data: values,
                backgroundColor: "rgba(0,255,136,0.6)",
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 800, easing: 'easeOutQuart' },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { color: "#aaa" },
                    grid: { color: "rgba(255,255,255,0.05)" }
                },
                x: {
                    ticks: { color: "#aaa" },
                    grid: { display: false }
                }
            },
            plugins: {
                legend: { labels: { color: "#ccc" } }
            }
        }
    });

    let healthNote = document.getElementById("healthChartNote");
    if (!healthNote) {
        healthNote = document.createElement("div");
        healthNote.id = "healthChartNote";
        healthNote.style.marginTop = "8px";
        healthNote.style.fontSize = "12px";
        healthNote.style.color = "#aaa";
        ctx.canvas.parentElement.appendChild(healthNote);
    }

    healthNote.innerText =
        "This chart compares health scores across vehicles. Lower bars indicate vehicles requiring maintenance attention.";
}

// ===============================
// Cost Forecast Chart
// ===============================
function renderCostForecast(labels, values) {
    const ctx = document.getElementById("fleetCostChart").getContext("2d");

    if (costChart) costChart.destroy();

    costChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Predicted Life (Years)",
                data: values,
                borderColor: "#ff8c00",
                backgroundColor: "rgba(255,140,0,0.1)",
                fill: true,
                tension: 0.4,
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 800, easing: 'easeOutQuart' },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: "#aaa" },
                    grid: { color: "rgba(255,255,255,0.05)" }
                },
                x: {
                    ticks: { color: "#aaa" },
                    grid: { display: false }
                }
            },
            plugins: {
                legend: { labels: { color: "#ccc" } }
            }
        }
    });

    let lifeNote = document.getElementById("lifeChartNote");
    if (!lifeNote) {
        lifeNote = document.createElement("div");
        lifeNote.id = "lifeChartNote";
        lifeNote.style.marginTop = "8px";
        lifeNote.style.fontSize = "12px";
        lifeNote.style.color = "#aaa";
        ctx.canvas.parentElement.appendChild(lifeNote);
    }

    lifeNote.innerText =
        "Predicted Life estimates remaining operational years. Lower values signal higher future maintenance risk.";
}