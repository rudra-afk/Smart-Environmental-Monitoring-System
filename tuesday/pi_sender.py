import time
import requests

# CHANGE THIS to your OpenStack VM Floating IP
VM_PUSH_URL = "http://<VM_FLOATING_IP>:5000/api/push"

# -----------------------------
# Replace these with your real sensor reads
# -----------------------------
def read_temperature_humidity_pressure():
# TODO: use your AHT20 + BMP280 reading code here
    temp = 25.0
    hum = 55.0
    pres = 1007.5
    return temp, hum, pres

def read_mq135_values():
# TODO: use MCP3008 MQ135 reading code here
    gas_raw = 450
    co2_ppm = 650 # your calculated value if you have it
    aqi = 80 # your estimated AQI if you have it
    return gas_raw, co2_ppm, aqi

def main():
    while True:
        try:
            temp, hum, pres = read_temperature_humidity_pressure()
            gas_raw, co2_ppm, aqi = read_mq135_values()

            payload = {
            "temperature": round(temp, 2),
            "humidity": round(hum, 2),
            "pressure": round(pres, 2),
            "gas_raw": int(gas_raw),
            "co2_ppm": float(co2_ppm),
            "aqi": float(aqi)
            }

            r = requests.post(VM_PUSH_URL, json=payload, timeout=5)
            print("PUSH:", r.status_code, r.text)

        except Exception as e:
            print("ERROR:", e)

time.sleep(2)

if __name__ == "__main__":main()