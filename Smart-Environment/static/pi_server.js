import express from "express";

const app = express();
const PORT = 3000;

app.get("/data", (req, res) => {
  res.set("Cache-Control", "no-store");

  res.json({
    temperature: 24 + Math.random(),
    humidity: 55 + Math.random(),
    pressure: 1012 + Math.random(),
    ecO2: 600 + Math.floor(Math.random() * 50),
    iaq: "Good",
    ts: Date.now()
  });
});

app.listen(PORT, () => {
  console.log("🍓 Pi server running on port", PORT);
});