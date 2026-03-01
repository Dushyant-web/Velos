requireAuth();

let allAlerts = [];
let filteredAlerts = [];
let vehiclesList = [];
let alertChart;

// ===============================
// Init
// ===============================
document.addEventListener("DOMContentLoaded", () => {
    loadVehicles();
    loadAlerts();
});

// ===============================
// Load Vehicles (for filter dropdown)
// ===============================
async function loadVehicles() {
    const res = await authFetch(`${BASE_URL}/vehicles`);
    if (!res.ok) return;

    vehiclesList = await res.json();

    const vehicleSelect = document.getElementById("vehicleFilter");

    vehiclesList.forEach(v => {
        const option = document.createElement("option");
        option.value = v.number_plate;
        option.textContent = `${v.name} (${v.number_plate})`;
        vehicleSelect.appendChild(option);
    });
}

// ===============================
// Load Alerts
// ===============================
async function loadAlerts() {
    const res = await authFetch(`${BASE_URL}/alerts`);
    if (!res.ok) return;

    const data = await res.json();

    allAlerts = data;
    filteredAlerts = [...allAlerts];

    renderSummary();
    renderTable();
    renderFrequencyChart();
}

// ===============================
// Summary Cards
// ===============================
function renderSummary() {
    const totalActive = allAlerts.filter(a => a.status === "Active").length;
    const critical = allAlerts.filter(a => a.severity === "Critical" && a.status === "Active").length;

    const today = new Date().toDateString();
    const resolvedToday = allAlerts.filter(a =>
        a.status === "Resolved" &&
        new Date(a.timestamp).toDateString() === today
    ).length;

    document.getElementById("totalAlerts").innerText = totalActive;
    document.getElementById("criticalAlerts").innerText = critical;
    document.getElementById("resolvedToday").innerText = resolvedToday;
}

// ===============================
// Table Rendering
// ===============================
function renderTable() {
    const tbody = document.querySelector("#alertsTable tbody");
    tbody.innerHTML = "";

    if (filteredAlerts.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align:center; padding:20px; color:#888;">
                    No alerts found.
                </td>
            </tr>
        `;
        return;
    }

    filteredAlerts.forEach(alert => {

        const severityClass = `risk-${alert.severity.toLowerCase()}`;

        tbody.innerHTML += `
            <tr>
                <td>${alert.vehicle_id}</td>
                <td>${alert.component || "--"}</td>
                <td>
                    <span class="risk-badge ${severityClass}">
                        ${alert.severity}
                    </span>
                </td>
                <td>${alert.description || "--"}</td>
                <td>${new Date(alert.timestamp).toLocaleString()}</td>
                <td>${alert.status}</td>
                <td>
                    ${alert.status === "Active"
                        ? `<button onclick="markResolved('${alert.id}')">Resolve</button>`
                        : "--"
                    }
                </td>
            </tr>
        `;
    });
}

// ===============================
// Filters
// ===============================
function applyAlertFilters() {
    const severity = document.getElementById("severityFilter").value;
    const status = document.getElementById("statusFilter").value;
    const vehicle = document.getElementById("vehicleFilter").value;

    filteredAlerts = allAlerts.filter(alert => {
        return (
            (!severity || alert.severity === severity) &&
            (!status || alert.status === status) &&
            (!vehicle || alert.vehicle_id === vehicle)
        );
    });

    renderTable();
}

// ===============================
// Mark Alert Resolved
// ===============================
async function markResolved(alertId) {
    const res = await authFetch(`${BASE_URL}/alerts/${alertId}/resolve`, {
        method: "POST"
    });

    if (!res.ok) return;

    // Update local state
    const alert = allAlerts.find(a => a.id === alertId);
    if (alert) alert.status = "Resolved";

    renderSummary();
    applyAlertFilters();
}

// ===============================
// Alert Frequency Chart
// ===============================
function renderFrequencyChart() {

    const last30Days = {};
    const now = new Date();

    for (let i = 29; i >= 0; i--) {
        const date = new Date();
        date.setDate(now.getDate() - i);
        const key = date.toISOString().split("T")[0];
        last30Days[key] = 0;
    }

    allAlerts.forEach(alert => {
        const dateKey = new Date(alert.timestamp).toISOString().split("T")[0];
        if (last30Days.hasOwnProperty(dateKey)) {
            last30Days[dateKey]++;
        }
    });

    const labels = Object.keys(last30Days);
    const values = Object.values(last30Days);

    // If no alert activity, show empty state instead of flat chart
    if (values.every(v => v === 0)) {
        const container = document.getElementById("alertFrequencyChart").parentElement;
        container.innerHTML = `
            <div style="text-align:center;color:#888;padding:60px 0;">
                No alert activity in last 30 days
            </div>
        `;
        return;
    }

    const ctx = document.getElementById("alertFrequencyChart").getContext("2d");

    if (alertChart) alertChart.destroy();

    alertChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Alerts per Day",
                data: values,
                borderColor: "#00ff88",
                backgroundColor: "rgba(0,255,136,0.1)",
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                x: {
                    ticks: {
                        maxTicksLimit: 7,
                        color: "#aaa"
                    },
                    grid: {
                        color: "rgba(255,255,255,0.05)"
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        color: "#aaa"
                    },
                    grid: {
                        color: "rgba(255,255,255,0.05)"
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: "#ccc"
                    }
                }
            }
        }
    });
}
