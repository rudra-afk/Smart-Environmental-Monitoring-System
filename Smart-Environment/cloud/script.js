async function loadData() {
const statusEl = document.getElementById("status");

try {
const res = await fetch("/api/data", { cache: "no-store" });
const json = await res.json();

if (!json.ok || !json.data) {
statusEl.textContent = "No data yet (waiting for Raspberry Pi to push).";
return;
}

const d = json.data;

document.getElementById("temp").textContent = (d.temperature ?? "--") + " °C";
document.getElementById("hum").textContent = (d.humidity ?? "--") + " %";
document.getElementById("pres").textContent = (d.pressure ?? "--") + " hPa";
document.getElementById("co2").textContent = (d.co2_ppm ?? "--");
document.getElementById("aqi").textContent = (d.aqi ?? "--");
document.getElementById("gas").textContent = (d.gas_raw ?? "--");

document.getElementById("ts").textContent = json.received_at ?? "--";
statusEl.textContent = "Live ✅";
} catch (e) {
statusEl.textContent = "Error connecting to server ❌";
}
}

loadData();
setInterval(loadData, 2000);