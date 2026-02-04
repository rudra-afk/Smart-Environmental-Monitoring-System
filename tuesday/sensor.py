import time, math, json
from statistics import mean
from collections import deque
import board, busio, digitalio
import adafruit_ahtx0
import adafruit_bmp280
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# NEW: send to cloud
import requests

# ----------------------------
# CONFIG (EDIT THIS)
# ----------------------------
CLOUD_INGEST_URL = "http://172.22.250.145:5000/api/ingest" # OpenStack floating IP (uni-internal)
API_KEY = "" # optional: set same key in cloud app.py, else leave ""

VCC = 5.0
RL = 10000.0
A = 116.6020682
B = -2.769034857
CAL_FILE = "mq135_cal.json"

VCC = 5.0
RL = 10000.0
A = 116.6020682
B = -2.769034857
CAL_FILE = "mq135_cal.json"

def rs_from_voltage(v):
    if v <= 0.001:
        return float("inf")
    return RL * (VCC / v - 1.0)

def eco2_from_ratio(ratio):
    if ratio <= 0 or not math.isfinite(ratio):
        return float("nan")
    ppm = A * (ratio ** B)
    return max(400.0, min(ppm, 5000.0))

def iaq_from_eco2(ppm):
    if ppm <= 600: return 50
    if ppm <= 800: return 100
    if ppm <= 1000: return 150
    if ppm <= 1500: return 200
    if ppm <= 2000: return 300
    if ppm <= 3000: return 400
    return 500

def load_r0():
    try:
        with open(CAL_FILE, "r") as f:
            return json.load(f)["R0"]
    except:
        return None

def save_r0(r0):
    with open(CAL_FILE, "w") as f:
        json.dump({"R0": r0, "ts": time.time()}, f, indent=2)

def calibrate(mq_voltage_fn, seconds=60, assumed_clean_ppm=400.0):
    samples = []
    for _ in range(seconds):
        v = mq_voltage_fn()
        samples.append(rs_from_voltage(v))
        time.sleep(1)
    rs_avg = mean(samples)
    ratio = (assumed_clean_ppm / A) ** (1.0 / B)
    r0 = rs_avg / ratio
    save_r0(r0)
    return r0

class SensorHub:
    def __init__(self, bmp_addr=0x77, history_seconds=15*60, sample_period=1.0):
        self.sample_period = sample_period
        self.history = deque(maxlen=int(history_seconds / sample_period))

        # I2C
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.aht = adafruit_ahtx0.AHTx0(self.i2c)
        self.bmp = adafruit_bmp280.Adafruit_BMP280_I2C(self.i2c, address=bmp_addr)
        self.bmp.sea_level_pressure = 1013.25

        # SPI + MCP3008
        self.spi = busio.SPI(board.SCLK, board.MOSI, board.MISO)
        self.cs = digitalio.DigitalInOut(board.CE0)
        self.mcp = MCP.MCP3008(self.spi, self.cs)
        self.mq = AnalogIn(self.mcp, MCP.P0)

        # MQ135 calibration
        self.r0 = load_r0()
        if self.r0 is None:
            self.r0 = rs_from_voltage(self.mq.voltage)

        self.latest = None
        self.running = False

    def do_calibrate(self, seconds=60):
        print(f"Calibration started for {seconds} seconds.")
        self.r0 = calibrate(lambda: self.mq.voltage, seconds=seconds, assumed_clean_ppm=400.0)
        print(f"Calibration completed. R0: {self.r0}")
        return self.r0


    def read_once(self):
        ts = time.time()

        aht_temp = float(self.aht.temperature)
        humidity = float(self.aht.relative_humidity)

        bmp_temp = float(self.bmp.temperature)
        pressure = float(self.bmp.pressure)

        mq_raw = int(self.mq.value)
        mq_volt = float(self.mq.voltage)

        rs = rs_from_voltage(mq_volt)
        ratio = rs / self.r0 if self.r0 else float("nan")
        eco2 = float(eco2_from_ratio(ratio))
        iaq = int(iaq_from_eco2(eco2))

        data = {
            "ts": ts,
            "aht_temp_c": aht_temp,
            "humidity_pct": humidity,
            "bmp_temp_c": bmp_temp,
            "pressure_hpa": pressure,
            "mq_raw": mq_raw,
            "mq_volt": mq_volt,
            "eco2_ppm": eco2,
            "iaq_index": iaq,
        }
        self.latest = data
        self.history.append(data)
        return data
    
        # NEW: send one payload to cloud
    def send_to_cloud(self, payload: dict) -> bool:
        headers = {"Content-Type": "application/json"}
        if API_KEY:
            headers["X-API-Key"] = API_KEY

        try:
            r = requests.post(CLOUD_INGEST_URL, json=payload, headers=headers, timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def loop(self):
        self.running = True
        while self.running:
            try:
                self.read_once()
            except Exception:
                pass
            time.sleep(self.sample_period)

    def stop(self):
        self.running = False

# OPTIONAL runner (so you can run sensor.py directly)
if __name__ == "__main__":
    hub = SensorHub(sample_period=2.0)
    print("Starting sensor loop. Sending to cloud:", CLOUD_INGEST_URL)
    hub.loop()