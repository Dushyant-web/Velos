requireAuth();

const urlParams = new URLSearchParams(window.location.search);
const vehicleId = urlParams.get("id");

if (!vehicleId) {
    alert("Vehicle ID missing");
    throw new Error("Vehicle ID missing");
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("vehicleTitle").innerText =
        `Vehicle Intelligence - ${vehicleId}`;
    loadVehicleData();
});

let trendDataGlobal = [];
let currentHealthGlobal = 0;

function formatYearsToYearMonth(decimalYears) {
    const years = Math.floor(decimalYears);
    const months = Math.round((decimalYears - years) * 12);

    if (years === 0) return `${months} months`;
    if (months === 0) return `${years} years`;

    return `${years} years ${months} months`;
}

async function loadVehicleData() {

    const healthRes = await authFetch(
        `${BASE_URL}/vehicle/${vehicleId}/health`
    );

    const trendRes = await authFetch(
        `${BASE_URL}/vehicle/${vehicleId}/health-trend`
    );

    if (!healthRes.ok || !trendRes.ok) return;

    const health = await healthRes.json();
    const trend = await trendRes.json();

    const recs = generateRecommendations(
        health.health_score,
        trend
    );



    currentHealthGlobal = health.health_score;
    trendDataGlobal = trend;

    const healthValue = health.health_score.toFixed(1);
    const badge = getPerformanceBadge(health.health_score);
    
    document.getElementById("currentHealth").innerHTML =
        `${healthValue}% <span class="performance-badge ${badge.toLowerCase()}">${badge}</span>`;

    const riskElement = document.getElementById("riskLevel");
    riskElement.innerText = health.risk_level;

    if (health.health_score < 30) {
        riskElement.style.color = "#ff4d4d";
    } else if (health.health_score < 50) {
        riskElement.style.color = "#ffa500";
    } else {
        riskElement.style.color = "#00ff88";
    }

    document.getElementById("lifeRemaining").innerText =
        formatYearsToYearMonth(health.predicted_life_years);

    renderUnifiedChart(trend, null);
    renderRecommendations(recs);
    generateAdvancedRecommendations(
        currentHealthGlobal,
        trendDataGlobal,
        health.risk_level
    );
}

async function runProjection() {

    const years = document.getElementById("projYears").value || 0;
    const months = document.getElementById("projMonths").value || 0;
    const hours = document.getElementById("projHours").value || 0;

    // FIX BUTTON SELECTION
    const btn = document.querySelector("#projRunBtn");

    const res = await authFetch(
        `${BASE_URL}/vehicle/${vehicleId}/project-life?years=${years}&months=${months}&hours=${hours}`
    );

    if (!res.ok) return;

    const data = await res.json();

    document.getElementById("projectionSummary").innerHTML = `
        <div class="projection-result-card">

            <div class="projection-header">
                Projection Results
            </div>

            <div class="projection-grid">

                <div class="projection-metric">
                    <div class="metric-label">Projected Health</div>
                    <div class="metric-value health">
                        ${data.projected_health_percentage.toFixed(1)}%
                    </div>
                </div>

                <div class="projection-metric">
                    <div class="metric-label">Projected Remaining Life</div>
                    <div class="metric-value life">
                        ${formatYearsToYearMonth(data.projected_life_remaining_years)}
                    </div>
                </div>

                <div class="projection-metric full-width">
                    <div class="metric-label">Estimated Failure Date</div>
                    <div class="metric-value date">
                        ${new Date(data.predicted_failure_date).toLocaleDateString()}
                    </div>
                </div>

            </div>

        </div>
    `;

    renderUnifiedChart(trendDataGlobal, data.projected_health_percentage);
}

function renderUnifiedChart(trendData, projectedHealth) {

    const labels = trendData.map(item =>
        new Date(item.timestamp).toLocaleTimeString()
    );

    const historicalHealth = trendData.map(item =>
        item.health_score
    );

    const lifeRemaining = trendData.map(item =>
        item.life_remaining_years
    );

    let projectionDataset = null;

    if (projectedHealth !== null) {

        labels.push("Projected");

        projectionDataset = {
            label: "Projected Health",
            data: [
                ...Array(historicalHealth.length - 1).fill(null),
                historicalHealth[historicalHealth.length - 1],
                projectedHealth
            ],
            borderColor: "#ffffff",
            borderDash: [6, 6],
            borderWidth: 2,
            tension: 0.4,
            fill: false,
            yAxisID: "yHealth"
        };
    }

    const ctx = document
        .getElementById("healthTrendChart")
        .getContext("2d");

    if (window.healthChart) {
        window.healthChart.destroy();
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, "rgba(0,255,136,0.4)");
    gradient.addColorStop(1, "rgba(0,255,136,0.05)");

    const dangerIndex = historicalHealth.findIndex(v => v < 30);

    window.healthChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Historical Health",
                    data: historicalHealth,
                    fill: true,
                    backgroundColor: gradient,
                    borderColor: "#00ff88",
                    borderWidth: 2,
                    tension: 0.4,
                    yAxisID: "yHealth",
                    pointRadius: 3,
                    pointHoverRadius: 6,
                },
                {
                    label: "Life Remaining (Years)",
                    data: lifeRemaining,
                    borderColor: "#00bfff",
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    yAxisID: "yLife",
                    pointRadius: 2,
                    pointHoverRadius: 5,
                },
                ...(projectionDataset ? [projectionDataset] : [])
            ]
        },
        options: {
            // 1️⃣ ADD BETTER INTERACTION MODE
            interaction: {
                mode: "index",
                intersect: false
            },
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 800 },
            scales: {
                yHealth: {
                    type: "linear",
                    position: "left",
                    min: 0,
                    max: 100,
                    ticks: { color: "#00ff88" },
                    grid: {
                        color: "rgba(255,255,255,0.05)"
                    }
                },
                yLife: {
                    type: "linear",
                    position: "right",
                    min: 0,
                    ticks: { color: "#00bfff" },
                    grid: {
                        drawOnChartArea: false,
                        color: "rgba(0,191,255,0.1)"
                    }
                },
                // 2️⃣ IMPROVE X-AXIS READABILITY
                x: {
                    ticks: {
                        color: "#888",
                        maxTicksLimit: 8,
                        autoSkip: true
                    },
                    grid: {
                        color: "rgba(255,255,255,0.03)"
                    }
                }
            },
            plugins: {
                legend: {
                    position: "top",
                    labels: {
                        color: "#e0e0e0",
                        boxWidth: 20,
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: "#111",
                    borderColor: "#333",
                    borderWidth: 1,
                    titleColor: "#fff",
                    bodyColor: "#ccc",
                    padding: 10,
                    displayColors: true,
                    // 3️⃣ ADD HEALTH DELTA TO TOOLTIP
                    callbacks: {
                        afterBody: function(context) {
                            const index = context[0].dataIndex;
                            if (index === 0) return "";

                            const current = historicalHealth[index];
                            const previous = historicalHealth[index - 1];
                            const delta = (current - previous).toFixed(1);

                            if (isNaN(delta)) return "";

                            const symbol = delta >= 0 ? "▲" : "▼";
                            return `Health Change: ${symbol} ${Math.abs(delta)}%`;
                        }
                    }
                }
            }
        },
        plugins: [

            // 🔴 Danger + Warning Zones
            {
                id: "zoneBackground",
                beforeDraw(chart) {
                    const { ctx, chartArea: { top, bottom, left, right }, scales: { yHealth } } = chart;

                    ctx.save();

                    // Danger (<30)
                    ctx.fillStyle = "rgba(255, 0, 0, 0.08)";
                    ctx.fillRect(
                        left,
                        yHealth.getPixelForValue(30),
                        right - left,
                        bottom - yHealth.getPixelForValue(30)
                    );

                    // Warning (30–50)
                    ctx.fillStyle = "rgba(255, 165, 0, 0.08)";
                    ctx.fillRect(
                        left,
                        yHealth.getPixelForValue(50),
                        right - left,
                        yHealth.getPixelForValue(30) - yHealth.getPixelForValue(50)
                    );

                    ctx.restore();
                }
            },

            // ⚠ Smart Danger Annotation
            {
                id: "dangerAnnotation",
                afterDatasetsDraw(chart) {

                    if (dangerIndex === -1) return;

                    const { ctx, scales: { x, yHealth } } = chart;

                    ctx.save();
                    ctx.fillStyle = "#ff4d4d";
                    ctx.font = "12px Arial";
                    ctx.fillText(
                        "⚠ Entered Danger Zone",
                        x.getPixelForValue(dangerIndex),
                        yHealth.getPixelForValue(30) - 10
                    );
                    ctx.restore();
                }
            },

            // 🔵 Future Divider
            {
                id: "futureDivider",
                afterDraw(chart) {

                    if (projectedHealth === null) return;

                    const { ctx, chartArea, scales: { x } } = chart;
                    const lastIndex = chart.data.labels.length - 1;

                    ctx.save();
                    ctx.setLineDash([4, 4]);
                    ctx.strokeStyle = "rgba(255,255,255,0.2)";
                    ctx.beginPath();
                    ctx.moveTo(x.getPixelForValue(lastIndex), chartArea.top);
                    ctx.lineTo(x.getPixelForValue(lastIndex), chartArea.bottom);
                    ctx.stroke();
                    ctx.restore();
                }
            }

        ]
    });
}



async function runScenarioComparison() {

    const years = document.getElementById("projYears").value || 1;
    const months = document.getElementById("projMonths").value || 0;
    const hours = document.getElementById("projHours").value || 0;

    const res = await authFetch(
        `${BASE_URL}/vehicle/${vehicleId}/project-life?years=${years}&months=${months}&hours=${hours}`
    );

    if (!res.ok) return;

    const baseline = await res.json();

    const normal = baseline.projected_health_percentage;

    // 🔴 Aggressive = Faster degradation
    const aggressive = Math.max(normal - 12, 0);

    // 🔵 Optimized = Improved efficiency
    const optimized = Math.min(normal + 8, 100);

    renderScenarioComparisonSim(normal, aggressive, optimized);
    renderScenarioSummarySim(normal, aggressive, optimized);
}


function renderScenarioComparisonSim(normal, aggressive, optimized) {

    const labels = trendDataGlobal.map(item =>
        new Date(item.timestamp).toLocaleTimeString()
    );

    labels.push("Future");

    const historicalHealth = trendDataGlobal.map(item =>
        item.health_score
    );

    const lifeRemaining = trendDataGlobal.map(item =>
        item.life_remaining_years
    );

    const ctx = document
        .getElementById("healthTrendChart")
        .getContext("2d");

    if (window.healthChart) {
        window.healthChart.destroy();
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, "rgba(0,255,136,0.4)");
    gradient.addColorStop(1, "rgba(0,255,136,0.05)");

    const lastHistorical = historicalHealth[historicalHealth.length - 1];

    window.healthChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [

                {
                    label: "Historical Health",
                    data: historicalHealth,
                    fill: true,
                    backgroundColor: gradient,
                    borderColor: "#00ff88",
                    borderWidth: 2,
                    tension: 0.4,
                    yAxisID: "yHealth"
                },

                {
                    label: "Life Remaining (Years)",
                    data: lifeRemaining,
                    borderColor: "#00bfff",
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    yAxisID: "yLife"
                },

                {
                    label: "Normal Usage",
                    data: [
                        ...Array(historicalHealth.length - 1).fill(null),
                        lastHistorical,
                        normal
                    ],
                    borderColor: "#ffffff",
                    borderDash: [6,6],
                    tension: 0.4,
                    yAxisID: "yHealth"
                },

                {
                    label: "Aggressive Driving",
                    data: [
                        ...Array(historicalHealth.length - 1).fill(null),
                        lastHistorical,
                        aggressive
                    ],
                    borderColor: "#ff4d4d",
                    borderDash: [6,6],
                    tension: 0.4,
                    yAxisID: "yHealth"
                },

                {
                    label: "Optimized Driving",
                    data: [
                        ...Array(historicalHealth.length - 1).fill(null),
                        lastHistorical,
                        optimized
                    ],
                    borderColor: "#00bfff",
                    borderDash: [6,6],
                    tension: 0.4,
                    yAxisID: "yHealth"
                }

            ]
        },
        options: {
            interaction: {
                mode: "index",
                intersect: false
            },
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                yHealth: {
                    type: "linear",
                    position: "left",
                    min: 0,
                    max: 100
                },
                yLife: {
                    type: "linear",
                    position: "right",
                    min: 0,
                    grid: { drawOnChartArea: false }
                }
            }
        },
        plugins: [

            // Danger & Warning Zones
            {
                id: "zoneBackground",
                beforeDraw(chart) {
                    const { ctx, chartArea: { top, bottom, left, right }, scales: { yHealth } } = chart;

                    ctx.save();

                    ctx.fillStyle = "rgba(255, 0, 0, 0.08)";
                    ctx.fillRect(
                        left,
                        yHealth.getPixelForValue(30),
                        right - left,
                        bottom - yHealth.getPixelForValue(30)
                    );

                    ctx.fillStyle = "rgba(255, 165, 0, 0.08)";
                    ctx.fillRect(
                        left,
                        yHealth.getPixelForValue(50),
                        right - left,
                        yHealth.getPixelForValue(30) - yHealth.getPixelForValue(50)
                    );

                    ctx.restore();
                }
            },

            // Future Divider
            {
                id: "futureDivider",
                afterDraw(chart) {
                    const { ctx, chartArea, scales: { x } } = chart;
                    const lastIndex = chart.data.labels.length - 1;

                    ctx.save();
                    ctx.setLineDash([4,4]);
                    ctx.strokeStyle = "rgba(255,255,255,0.2)";
                    ctx.beginPath();
                    ctx.moveTo(x.getPixelForValue(lastIndex), chartArea.top);
                    ctx.lineTo(x.getPixelForValue(lastIndex), chartArea.bottom);
                    ctx.stroke();
                    ctx.restore();
                }
            }

        ]
    });
}

function renderScenarioSummarySim(normal, aggressive, optimized) {

    const years = parseInt(document.getElementById("projYears").value || 1);

    const normalCost = calculateMaintenanceCost(normal, "normal", years);
    const aggressiveCost = calculateMaintenanceCost(aggressive, "aggressive", years);
    const optimizedCost = calculateMaintenanceCost(optimized, "optimized", years);

    const savings = aggressiveCost - optimizedCost;
    const diff = (optimized - aggressive).toFixed(1);

    document.getElementById("scenarioSummary").innerHTML = `
        <div class="scenario-card">

            <h3>Driving Impact & Cost Analysis</h3>

            <div class="scenario-grid">

                <div class="scenario-box normal">
                    <div class="scenario-title">Normal</div>
                    <div class="scenario-value">${normal.toFixed(1)}%</div>
                    <div class="scenario-cost">
                        <div class="cost-label">Estimated Maintenance</div>
                        <div class="cost-value">
                            <span class="currency">₹</span>
                            <span class="amount">${normalCost.toLocaleString()}</span>
                        </div>
                    </div>
                </div>

                <div class="scenario-box aggressive">
                    <div class="scenario-title">Aggressive</div>
                    <div class="scenario-value">${aggressive.toFixed(1)}%</div>
                    <div class="scenario-cost">
                        <div class="cost-label">Estimated Maintenance</div>
                        <div class="cost-value">
                            <span class="currency">₹</span>
                            <span class="amount">${aggressiveCost.toLocaleString()}</span>
                        </div>
                    </div>
                </div>

                <div class="scenario-box optimized">
                    <div class="scenario-title">Optimized</div>
                    <div class="scenario-value">${optimized.toFixed(1)}%</div>
                    <div class="scenario-cost">
                        <div class="cost-label">Estimated Maintenance</div>
                        <div class="cost-value">
                            <span class="currency">₹</span>
                            <span class="amount">${optimizedCost.toLocaleString()}</span>
                        </div>
                    </div>
                </div>

            </div>

            <div class="scenario-insight">
                Optimized driving preserves <strong>${diff}% more health</strong>
                and saves approximately <strong>₹ ${savings.toLocaleString()}</strong>
                over ${years} year(s).
            </div>

        </div>
    `;
}

function calculateMaintenanceCost(health, mode, years) {

    const baseCostPerYear = 15000;

    let wearMultiplier = 1;

    if (mode === "aggressive") wearMultiplier = 1.4;
    if (mode === "optimized") wearMultiplier = 0.85;

    const healthFactor = (100 - health) / 100;

    const projectedCost =
        baseCostPerYear *
        years *
        (1 + healthFactor) *
        wearMultiplier;

    return Math.round(projectedCost);
}

function generateRecommendations(health, trendData) {

    const recommendations = [];

    const lastFive = trendData.slice(-5);
    const slope =
        lastFive[lastFive.length - 1].health_score -
        lastFive[0].health_score;

    // 🔴 Critical Engine Condition
    if (health < 30) {
        recommendations.push({
            component: "Engine System",
            message: "Immediate full diagnostic inspection required.",
            severity: "High",
            eta: "Within 7 days",
            priority: 1
        });
    }

    // 🟠 Brake Wear Simulation
    if (health < 50) {
        recommendations.push({
            component: "Brake System",
            message: "Brake pads likely approaching wear limit.",
            severity: "Medium",
            eta: "Within 30 days",
            priority: 2
        });
    }

    // 🟡 Battery Degradation Trend
    if (slope < -5) {
        recommendations.push({
            component: "Battery & Electrical",
            message: "Rapid health decline detected. Check charging system.",
            severity: "Medium",
            eta: "Within 14 days",
            priority: 2
        });
    }

    // 🟢 Stable Condition
    if (health > 80 && slope >= -2) {
        recommendations.push({
            component: "General Maintenance",
            message: "Vehicle operating normally. Continue routine servicing.",
            severity: "Low",
            eta: "Next scheduled service",
            priority: 3
        });
    }

    // 🔵 Tire Performance Simulation
    if (health >= 50 && health < 80) {
        recommendations.push({
            component: "Tire & Suspension",
            message: "Monitor tire alignment and suspension wear.",
            severity: "Low",
            eta: "Next 60 days",
            priority: 3
        });
    }

    // 🔥 Sort by priority (AI-style decision ordering)
    recommendations.sort((a, b) => a.priority - b.priority);

    return recommendations;
}

function renderRecommendations(recommendations) {

    const container = document.getElementById("recommendationsContainer");
    if (!container) return;

    if (!recommendations.length) {
        container.innerHTML = `
            <div class="recommendation-card empty">
                <h3>Recommended Actions</h3>
                <p>No immediate actions required. Vehicle condition is stable.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="recommendation-card">
            <h3>Recommended Actions</h3>
            <div class="recommendation-list">
                ${recommendations.map(r => `
                    <div class="recommendation-item ${r.severity.toLowerCase()}">
                        <div class="rec-header">
                            <span class="rec-component">${getComponentIcon(r.component)} ${r.component}</span>
                            <span class="rec-severity severity-${r.severity.toLowerCase()}">${r.severity}</span>
                        </div>
                        <div class="rec-message">${r.message}</div>
                        <div class="rec-meta">
                            Action Timeline: ${r.eta}
                        </div>
                    </div>
                `).join("")}
            </div>
        </div>
    `;
}


function getPerformanceBadge(health) {

    if (health >= 80) return "Excellent";
    if (health >= 50) return "Stable";
    if (health >= 30) return "Warning";
    return "Critical";
}

function getComponentIcon(component) {

    if (component.includes("Engine")) return "⚙️";
    if (component.includes("Brake")) return "🛑";
    if (component.includes("Battery")) return "🔋";
    if (component.includes("Tire")) return "🛞";

    return "🔧";
}