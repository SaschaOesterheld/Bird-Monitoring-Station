# BiMoWebsite/config.py
from pathlib import Path

# Datenbank-Pfad (gleiche Datei wie Mockup)
DB_PATH = Path(__file__).resolve().parent.parent / "birdnet-mini" / "live_data.db"

# Flask-Einstellungen
FLASK_HOST = "0.0.0.0"     # auf allen Schnittstellen lauschen
FLASK_PORT = 5001           # 5000 ist bereits belegt

# SSE-Update-Intervall (Sekunden)
SSE_INTERVAL = 1.0

# Wieviele Minuten Temperaturhistorie beim ersten Laden der Seite abgerufen werden
HISTORY_MINUTES = 30