import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.normpath(os.path.join(BASE_DIR, os.pardir, os.pardir, "SQL", "EKK.db"))


def lade_fahrer():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Datenbankpfad nicht gefunden: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT vorname, nachname FROM fahrer WHERE status = 1 ORDER BY vorname, nachname")
    rows = cursor.fetchall()
    conn.close()
    return [f"{vorname} {nachname}" for vorname, nachname in rows]


def lade_fahrzeuge():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Datenbankpfad nicht gefunden: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT kennzeichen FROM fahrzeuge ORDER BY kennzeichen")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]
