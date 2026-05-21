from flask import Flask, jsonify, render_template, request
from threading import Thread
from sensor import SensorHub
from flask_cors import CORS  # CORS to allow cross-origin requests
from collections import deque
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# -----------------------
# Storage (in-memory)
# -----------------------
HISTORY_MAX = 2000
history = deque(maxlen=HISTORY_MAX)
latest = None

# -----------------------
# Optional simple auth
# (set same key on Pi sender)
# -----------------------
API_KEY = os.environ.get("API_KEY", "") # leave empty to disable

def auth_ok(req):
    if not API_KEY:
        return True
    return req.headers.get("X-API-Key", "") == API_KEY

# Initialize the sensor hub
hub = SensorHub(bmp_addr=0x77, history_seconds=15 * 60, sample_period=1.0)

# Start the backgpip3 install adafruit-circuitpython-mcp3xxxround sensor loop in a separate thread
def start_sensor_loop():
    t = Thread(target=hub.loop, daemon=True)
    t.start()

start_sensor_loop()

@app.route("/")
def index():
    return render_template("index.html")

# -----------------------
# NEW: Pi -> Cloud ingest
# -----------------------
@app.route("/api/ingest", methods=["POST"])
def api_ingest():
    global latest

    if not auth_ok(request):
            return jsonify({"ok": False, "error": "unauthorized"}), 401

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"ok": False, "error": "invalid_json"}), 400

    # Add cloud timestamp + source IP (nice for debugging/report)
    body["cloud_ts"] = datetime.utcnow().isoformat()
    body["source_ip"] = request.remote_addr

    latest = body
    history.append(body)

    return jsonify({"ok": True})

@app.route("/api/latest")
def api_latest():
    if hub.latest is None:
        return jsonify({"status": "warming_up"}), 200
    return jsonify(hub.latest)

@app.route("/api/history")
def api_history():
    n = request.args.get("n", default=None, type=int)
    data = list(hub.history)
    if n is not None and n > 0:
        data = data[-n:]
    return jsonify(data)

@app.route("/api/calibrate", methods=["POST"])
def api_calibrate():
    # Get the request data (seconds for calibration)
    body = request.get_json(silent=True) or {}
    seconds = int(body.get("seconds", 60))

    try:
        # Start the calibration process
        r0 = hub.do_calibrate(seconds=seconds)

        # Return success response with the new calibration value (R0)
        return jsonify({"ok": True, "R0": r0})
    except Exception as e:
        # Handle errors during calibration
        print(f"Calibration error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
