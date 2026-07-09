# BiMoMockup/database.py
import sqlite3
from config import DB_PATH

def get_connection():
    """Stellt eine Verbindung zur SQLite-DB her (WAL-Modus für parallelen Zugriff)."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Legt die benötigten Tabellen an, falls sie noch nicht existieren."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS temperature_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL NOT NULL,
            measured_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS bird_detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            species TEXT NOT NULL,
            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Tabelle für Steuerbefehle (optional, später)
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT NOT NULL,
            params TEXT,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

def insert_temperature(temp):
    """Schreibt einen neuen Temperaturwert."""
    conn = get_connection()
    conn.execute("INSERT INTO temperature_readings (temperature) VALUES (?)", (temp,))
    conn.commit()
    conn.close()

def insert_bird_detection(species):
    """Schreibt eine neue Vogel-Erkennung."""
    conn = get_connection()
    conn.execute("INSERT INTO bird_detections (species) VALUES (?)", (species,))
    conn.commit()
    conn.close()