document.addEventListener("DOMContentLoaded", function () {
    const fmt = (v, unit="") => (v === null || v === undefined) ? "--" : `${v}${unit}`;

    async function getJSON(url) {
        const r = await fetch(url);
        return await r.json();
    }

    function mkLineChart(canvasId, label) {
        const ctx = document.getElementById(canvasId);
        if (ctx) {
            return new Chart(ctx, {
                type: "line",
                data: { labels: [], datasets: [{ label, data: [] }] },
                options: {
                    animation: false,
                    responsive: true,
                    scales: { x: { display: false } }
                }
            });
        } else {
            console.error(`Canvas with id ${canvasId} not found`);
            return null;
        }
    }

    const tempChart = mkLineChart("tempChart", "Temp (AHT20 °C)");
    const humChart = mkLineChart("humChart", "Humidity (%)");
    const presChart = mkLineChart("presChart", "Pressure (hPa)");
    const mqChart = new Chart(document.getElementById("mqChart"), {
        type: "line",
        data: {
            labels: [],
            datasets: [
                { label: "MQ Voltage (V)", data: [] },
                { label: "eCO₂ (ppm)", data: [] },
            ]
        },
        options: { animation: false, responsive: true, scales: { x: { display: false } } }
    });

    function pushPoint(chart, label, value, max=180) {
        if (chart) {
            chart.data.labels.push(label);
            chart.data.datasets[0].data.push(value);
            if (chart.data.labels.length > max) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }
            chart.update();
        }
    }

    function pushPoint2(chart, label, v1, v2, max=180) {
        if (chart) {
            chart.data.labels.push(label);
            chart.data.datasets[0].data.push(v1);
            chart.data.datasets[1].data.push(v2);
            if (chart.data.labels.length > max) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
                chart.data.datasets[1].data.shift();
            }
            chart.update();
        }
    }

    async function refresh() {
        const latest = await getJSON("/api/latest");
        if (latest.status === "warming_up") return;

        document.getElementById("tAht").textContent = fmt(latest.aht_temp_c?.toFixed(2), " °C");
        document.getElementById("hum").textContent = fmt(latest.humidity_pct?.toFixed(1), " %");
        document.getElementById("pres").textContent = fmt(latest.pressure_hpa?.toFixed(1), " hPa");
        document.getElementById("eco2").textContent = fmt(Math.round(latest.eco2_ppm), " ppm");
        document.getElementById("iaq").textContent = fmt(latest.iaq_index);

        const label = new Date(latest.ts * 1000).toLocaleTimeString();

        pushPoint(tempChart, label, latest.aht_temp_c);
        pushPoint(humChart, label, latest.humidity_pct);
        pushPoint(presChart, label, latest.pressure_hpa);
        pushPoint2(mqChart, label, latest.mq_volt, latest.eco2_ppm);
    }

    document.getElementById("calBtn").addEventListener("click", async () => {
        document.getElementById("calBtn").disabled = true; // Disable the button during calibration
        document.getElementById("calBtn").textContent = "Calibrating..."; // Update button text

        try {
            // Send the POST request to start the calibration
            const response = await fetch("/api/calibrate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ seconds: 60 }) // Calibrate for 60 seconds
            });

            const result = await response.json();

            // Once calibration is done, display success message
            if (result.ok) {
                document.getElementById("calBtn").textContent = "Calibration Complete!";
            } else {
                document.getElementById("calBtn").textContent = "Calibration Failed!";
            }
        } catch (error) {
            console.error("Error during calibration:", error);
            document.getElementById("calBtn").textContent = "Calibration Failed!";
        } finally {
            document.getElementById("calBtn").disabled = false; // Re-enable the button after calibration
        }
    });

    setInterval(refresh, 1000);
    refresh();
});
