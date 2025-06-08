import sqlite3
import pandas as pd
import glob, os, re

# --- Pfade anpassen ---
DB_PATH = r"C:\EKK\Skripts\windows_app\data\EKK.db"
CSV_DIR = r"C:\EKK\Skripts\windows_app\data"

# Verbindung zur SQLite-DB aufbauen
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Gemeinsames Tabellen-Schema für beide Plattformen
# Gleiche Header für 'umsatz_bolt' und 'umsatz_uber'
table_schema = """
CREATE TABLE IF NOT EXISTS {table_name} (
    Driver TEXT,
    kalenderwoche TEXT,
    barumsatz REAL,
    bankomatumsatz REAL,
    trinkgeld_gesamt REAL,
    trinkgeld_nonbar REAL,
    gesamtumsatz REAL,
    UNIQUE(Driver, kalenderwoche)
);
"""
# Tabellen neu anlegen (vorher löschen)
cursor.execute("DROP TABLE IF EXISTS umsatz_bolt;")
cursor.execute(table_schema.format(table_name="umsatz_bolt"))

cursor.execute("DROP TABLE IF EXISTS umsatz_uber;")
cursor.execute(table_schema.format(table_name="umsatz_uber"))

# Bolt-Daten importieren
for csv_file in glob.glob(os.path.join(CSV_DIR, "Bolt_KW*.csv")):
    fn = os.path.basename(csv_file)
    # Kalenderwoche aus Dateiname extrahieren
    m = re.match(r"Bolt_KW(\d+)\.csv", fn)
    if not m:
        continue
    week = m.group(1)

    df = pd.read_csv(csv_file, encoding="utf-8-sig")
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Spalten umbenennen für einheitliches Schema
    df["Driver"] = df.iloc[:, 0]
    df["kalenderwoche"] = week
    df["barumsatz"] = df["Collected cash|€"]
    df["bankomatumsatz"] = df["Gross earnings (in-app payment)|€"]
    df["trinkgeld_gesamt"] = df["Rider tips|€"]
    df["trinkgeld_nonbar"] = df["Rider tips|€"]
    df["gesamtumsatz"] = df["Net earnings|€"]

    cols = ["Driver", "kalenderwoche", "barumsatz", "bankomatumsatz", "trinkgeld_gesamt", "trinkgeld_nonbar", "gesamtumsatz"]
    df[cols].to_sql(name="umsatz_bolt", con=conn, if_exists="append", index=False)
    print(f"Importiert in umsatz_bolt: {fn}")

# Uber-Daten importieren
for csv_file in glob.glob(os.path.join(CSV_DIR, "Uber_KW*.csv")):
    fn = os.path.basename(csv_file)
    m = re.match(r"Uber_KW(\d+)\.csv", fn)
    if not m:
        continue
    week = m.group(1)

    df = pd.read_csv(csv_file, encoding="utf-8-sig")
    df["Driver"] = df["Nachname des Fahrers"] + " " + df["Vorname des Fahrers"]
    df["kalenderwoche"] = week
    df["barumsatz"] = df["Eingenommenes Bargeld"]
    df["bankomatumsatz"] = df["Gesamtumsätze"] - df["Eingenommenes Bargeld"]
    df["trinkgeld_gesamt"] = 0
    df["trinkgeld_nonbar"] = 0
    df["gesamtumsatz"] = df["Gesamtumsätze"]

    cols = ["Driver", "kalenderwoche", "barumsatz", "bankomatumsatz", "trinkgeld_gesamt", "trinkgeld_nonbar", "gesamtumsatz"]
    df[cols].to_sql(name="umsatz_uber", con=conn, if_exists="append", index=False)
    print(f"Importiert in umsatz_uber: {fn}")

# Änderungen speichern und Verbindung schließen
conn.commit()
conn.close()
