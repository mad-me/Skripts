import os
import glob
import re
import pandas as pd
import sqlite3

print("🔢 Eingebaute SQLite-Version:", sqlite3.sqlite_version)

# === Konfiguration ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../SQL/EKK.db"))
CSV_DIR = os.path.abspath(os.path.join(BASE_DIR, "../data/archive"))
BOLT_PATTERN = os.path.join(CSV_DIR, "Bolt_KW*.csv")
UBER_PATTERN = os.path.join(CSV_DIR, "Uber_KW*.csv")

print("📁 Aktive Datenbank:", DB_PATH)
print("📂 Suchpfad für CSVs:", CSV_DIR)
print("🔍 Bolt-Dateien:", BOLT_PATTERN)
print("🔍 Uber-Dateien:", UBER_PATTERN)

# === Verbindung zur Datenbank ===
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# === Tabellen-Schema ===
table_schema = """
CREATE TABLE IF NOT EXISTS {table} (
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

for tbl in ("umsatz_bolt", "umsatz_uber"):
    cursor.execute(table_schema.format(table=tbl))
    print(f"🗄️ Tabelle '{tbl}' ist bereit (bestehend oder neu erstellt).")

# === Bolt-Daten importieren ===
cnt_bolt = 0
bolt_files = glob.glob(BOLT_PATTERN)
print(f"📦 Gefundene Bolt-Dateien: {bolt_files}")

for csv_file in bolt_files:
    fn = os.path.basename(csv_file)
    match = re.match(r"Bolt_KW(\d+)\.csv", fn)
    if not match:
        continue
    week = match.group(1)
    df = pd.read_csv(csv_file, encoding="utf-8-sig")
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    df["Driver"] = df.iloc[:, 0]
    df["kalenderwoche"] = week
    df["barumsatz"] = df.get("Collected cash|€", 0).astype(float)
    df["bankomatumsatz"] = df.get("Gross earnings (in-app payment)|€", 0).astype(float)
    df["trinkgeld_gesamt"] = df.get("Rider tips|€", 0).astype(float)
    df["trinkgeld_nonbar"] = df.get("Rider tips|€", 0).astype(float)
    df["gesamtumsatz"] = df.get("Net earnings|€", 0).astype(float)

    cols = ["Driver", "kalenderwoche", "barumsatz", "bankomatumsatz",
            "trinkgeld_gesamt", "trinkgeld_nonbar", "gesamtumsatz"]

    try:
        for _, row in df[cols].iterrows():
            driver = row["Driver"]
            kw = row["kalenderwoche"]

            cursor.execute("""
                SELECT 1 FROM umsatz_bolt WHERE Driver = ? AND kalenderwoche = ?
            """, (driver, kw))
            exists = cursor.fetchone() is not None

            if exists:
                cursor.execute("""
                    UPDATE umsatz_bolt
                    SET barumsatz = ?, bankomatumsatz = ?, trinkgeld_gesamt = ?, 
                        trinkgeld_nonbar = ?, gesamtumsatz = ?
                    WHERE Driver = ? AND kalenderwoche = ?
                """, (
                    row["barumsatz"], row["bankomatumsatz"], row["trinkgeld_gesamt"],
                    row["trinkgeld_nonbar"], row["gesamtumsatz"],
                    driver, kw
                ))
            else:
                cursor.execute("""
                    INSERT INTO umsatz_bolt (Driver, kalenderwoche, barumsatz, bankomatumsatz,
                                             trinkgeld_gesamt, trinkgeld_nonbar, gesamtumsatz)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, tuple(row[cols]))

        print(f"✅ Importiert Bolt: {fn}")
        cnt_bolt += len(df)

    except Exception as e:
        print(f"❌ Fehler beim Import von {fn}: {e}")

print(f"📈 Gesamt Bolt-Zeilen importiert: {cnt_bolt}")

# === Uber-Daten importieren ===
cnt_uber = 0
uber_files = glob.glob(UBER_PATTERN)
print(f"📦 Gefundene Uber-Dateien: {uber_files}")

for csv_file in uber_files:
    fn = os.path.basename(csv_file)
    match = re.match(r"Uber_KW(\d+)\.csv", fn)
    if not match:
        continue
    week = match.group(1)
    df = pd.read_csv(csv_file, encoding="utf-8-sig")

    df["Driver"] = df.get("Nachname des Fahrers", "") + " " + df.get("Vorname des Fahrers", "")
    df["kalenderwoche"] = week
    df["barumsatz"] = df.get("Eingenommenes Bargeld", 0).astype(float)
    gesamt = df.get("Gesamtumsätze", 0).astype(float)
    df["bankomatumsatz"] = (gesamt - df["barumsatz"]).astype(float)
    df["trinkgeld_gesamt"] = 0.0
    df["trinkgeld_nonbar"] = 0.0
    df["gesamtumsatz"] = gesamt

    cols = ["Driver", "kalenderwoche", "barumsatz", "bankomatumsatz",
            "trinkgeld_gesamt", "trinkgeld_nonbar", "gesamtumsatz"]

    try:
        for _, row in df[cols].iterrows():
            driver = row["Driver"]
            kw = row["kalenderwoche"]

            cursor.execute("""
                SELECT 1 FROM umsatz_uber WHERE Driver = ? AND kalenderwoche = ?
            """, (driver, kw))
            exists = cursor.fetchone() is not None

            if exists:
                cursor.execute("""
                    UPDATE umsatz_uber
                    SET barumsatz = ?, bankomatumsatz = ?, trinkgeld_gesamt = ?, 
                        trinkgeld_nonbar = ?, gesamtumsatz = ?
                    WHERE Driver = ? AND kalenderwoche = ?
                """, (
                    row["barumsatz"], row["bankomatumsatz"], row["trinkgeld_gesamt"],
                    row["trinkgeld_nonbar"], row["gesamtumsatz"],
                    driver, kw
                ))
            else:
                cursor.execute("""
                    INSERT INTO umsatz_uber (Driver, kalenderwoche, barumsatz, bankomatumsatz,
                                             trinkgeld_gesamt, trinkgeld_nonbar, gesamtumsatz)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, tuple(row[cols]))

        print(f"✅ Importiert Uber: {fn}")
        cnt_uber += len(df)

    except Exception as e:
        print(f"❌ Fehler beim Import von {fn}: {e}")

print(f"📈 Gesamt Uber-Zeilen importiert: {cnt_uber}")

# === Abschließen ===
conn.commit()
conn.close()
print("🎉 Import abgeschlossen.")
