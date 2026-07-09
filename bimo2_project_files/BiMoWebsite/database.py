# BiMoWebsite/database.py
import sqlite3
from datetime import datetime, timedelta
from config import DB_PATH, HISTORY_MINUTES

def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def get_latest_bird():
    """Letzte Vogel-Erkennung (Art und Zeitpunkt)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT species, detected_at FROM bird_detections ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row:
        return {"species": row["species"], "detected_at": row["detected_at"]}
    return None

def get_latest_temperature():
    """Letzter Temperaturwert (Wert und Zeitpunkt)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT temperature, measured_at FROM temperature_readings ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row:
        return {"temperature": row["temperature"], "measured_at": row["measured_at"]}
    return None

def get_temperature_history(minutes=HISTORY_MINUTES):
    """Temperaturdaten der letzten `minutes` Minuten."""
    since = datetime.utcnow() - timedelta(minutes=minutes)
    conn = get_connection()
    rows = conn.execute(
        "SELECT temperature, measured_at FROM temperature_readings "
        "WHERE measured_at >= ? ORDER BY measured_at ASC",
        (since.strftime("%Y-%m-%d %H:%M:%S"),)
    ).fetchall()
    conn.close()
    return [{"temperature": r["temperature"], "measured_at": r["measured_at"]} for r in rows]