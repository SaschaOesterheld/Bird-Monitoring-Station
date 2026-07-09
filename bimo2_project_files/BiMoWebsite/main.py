# BiMoWebsite/main.py
import json
import time
from flask import Flask, render_template, Response, jsonify, stream_with_context
from config import FLASK_HOST, FLASK_PORT, SSE_INTERVAL, HISTORY_MINUTES
from database import get_latest_bird, get_latest_temperature, get_temperature_history

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", history_minutes=HISTORY_MINUTES)

@app.route("/api/latest")
def latest():
    """Gibt die aktuellsten Werte als JSON zurück (für Initialisierung)."""
    bird = get_latest_bird()
    temp = get_latest_temperature()
    return jsonify({
        "bird": bird,
        "temperature": temp
    })

@app.route("/api/history")
def history():
    """Temperatur-Historie der letzten HISTORY_MINUTES."""
    data = get_temperature_history()
    return jsonify(data)

@app.route("/stream")
def stream():
    """SSE-Endpunkt: sendet regelmäßig aktuelle Werte."""
    def event_stream():
        # Beim ersten Verbinden initiale Daten senden (optional)
        # Wir lassen den Client die ersten Daten per /api/latest holen.
        while True:
            bird = get_latest_bird()
            temp = get_latest_temperature()
            payload = {
                "bird": bird,
                "temperature": temp,
                "timestamp": time.time()  # clientseitig zur Orientierung
            }
            yield f"data: {json.dumps(payload)}\n\n"
            time.sleep(SSE_INTERVAL)

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream"
    )

if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=True)