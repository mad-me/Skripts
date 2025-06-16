import sqlite3
from config import DB_PATH

def get_connection():
    return sqlite3.connect(DB_PATH)

def lade_fahrer():
    with get_connection() as conn:
        return [
            f"{v} {n}"
            for v, n in conn.execute("SELECT vorname, nachname FROM fahrer WHERE status = 1")
        ]

def lade_fahrzeuge():
    with get_connection() as conn:
        return [r[0] for r in conn.execute("SELECT kennzeichen FROM fahrzeuge")]

# Weitere Queries können einfach hier ergänzt werden...
