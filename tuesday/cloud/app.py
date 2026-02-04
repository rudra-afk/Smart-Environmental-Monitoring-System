from flask import Flask, jsonify, request, render_template
from datetime import datetime, timezone

app = Flask(__name__)

# Stores the latest sensor data pushed by Raspberry Pi
LATEST = {
"data": None,
"received_at": None
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/data", methods=["GET"])
def api_data():
    # dashboard reads from here
        if LATEST["data"] is None:
            return jsonify({
        "ok": False,
        "message": "No data received yet. Make sure Raspberry Pi is posting to /api/push",
        "received_at": None,
        "data": None
        }), 200

        return jsonify({
    "ok": True,
    "received_at": LATEST["received_at"],
    "data": LATEST["data"]
    }), 200

@app.route("/api/push", methods=["POST"])
def api_push():
# Raspberry Pi posts to here
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
     return jsonify({"ok": False, "error": "Invalid JSON"}), 400

    # OPTIONAL: minimal validation (you can add more keys later)
    # We'll accept any dict, but you can enforce expected keys:
    # expected = {"temperature","humidity","pressure","gas_raw","co2_ppm","aqi"}
    # if not expected.issubset(payload.keys()): ...

    LATEST["data"] = payload
    LATEST["received_at"] = datetime.now(timezone.utc).isoformat()

    return jsonify({"ok": True}), 200

if __name__ == "__main__":
# IMPORTANT for OpenStack access
    app.run(host="0.0.0.0", port=5000, debug=False)