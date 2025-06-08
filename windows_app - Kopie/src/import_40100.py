import sqlite3
import pandas as pd
import difflib
import os

# === Konfiguration ===
DB_PATH = "EKK.db"
CSV_PATH = "40100_aggregierte_umsätze_pro_fahrzeug.csv"

print("📁 Aktive Datenbank:", os.path.abspath(DB_PATH))
print("📄 Eingelesene Datei:", os.path.abspath(CSV_PATH))

# === Verbindung zur SQLite-Datenbank ===
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# === Tabellen erstellen (falls nicht vorhanden) ===
cursor.execute("""
CREATE TABLE IF NOT EXISTS fahrzeuge (
    kennung INTEGER PRIMARY KEY,
    kennzeichen TEXT NOT NULL UNIQUE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS umsatz (
    fahrzeug_kennung TEXT,
    kalenderwoche TEXT,
    barumsatz REAL,
    bankomatumsatz REAL,
    trinkgeld_gesamt REAL,
    trinkgeld_nonbar REAL,
    plattform TEXT,
    gesamtumsatz REAL,
    UNIQUE(fahrzeug_kennung, kalenderwoche),
    FOREIGN KEY (fahrzeug_kennung) REFERENCES fahrzeuge(kennzeichen)
);
""")

# === Neue Spalte gesamtumsatz hinzufügen (falls noch nicht vorhanden) ===
try:
    cursor.execute("ALTER TABLE umsatz ADD COLUMN gesamtumsatz REAL;")
    print("➕ Spalte 'gesamtumsatz' wurde hinzugefügt.")
except sqlite3.OperationalError:
    print("ℹ️ Spalte 'gesamtumsatz' existiert bereits.")

# === CSV einlesen ===
df = pd.read_csv(CSV_PATH)
print("📊 Zeilen in CSV:", len(df))

# === Vorhandene Fahrzeugkennzeichen laden ===
cursor.execute("SELECT kennzeichen FROM fahrzeuge")
kennungsliste = [str(row[0]) for row in cursor.fetchall()]

# === Importieren ===
importierte_zeilen = 0
uebersprungene_zeilen = 0

for _, row in df.iterrows():
    rohwert = str(row['Fahrzeug']).strip()
    kennzeichen = rohwert

    if not kennzeichen.startswith("W"):
        kennzeichen = "W" + kennzeichen
    if not kennzeichen.endswith("TX"):
        kennzeichen = kennzeichen + "TX"

    if kennzeichen in kennungsliste:
        fahrzeug_kennung = kennzeichen
    else:
        similar = difflib.get_close_matches(str(kennzeichen), kennungsliste, n=1, cutoff=0.85)
        if similar:
            vorschlag = similar[0]
            bestätigung = input(
                f"❓ Ähnlicher Eintrag gefunden: '{kennzeichen}' ≈ '{vorschlag}'. Übernehmen? (j/n): ").strip().lower()
            if bestätigung == 'j':
                fahrzeug_kennung = vorschlag
            else:
                fahrzeug_kennung = kennzeichen
        else:
            print(f"❓ Fahrzeugkennung '{kennzeichen}' nicht gefunden.")
            eingabe = input(
                f"Bitte Verkehrskennzeichen für '{rohwert}' eingeben (oder Enter für '{kennzeichen}'): ").strip()
            if eingabe:
                if not eingabe.startswith("W"):
                    eingabe = "W" + eingabe
                if not eingabe.endswith("TX"):
                    eingabe = eingabe + "TX"
                fahrzeug_kennung = eingabe
            else:
                fahrzeug_kennung = kennzeichen

    fahrzeug_kennung = str(fahrzeug_kennung).strip()

    # Existierenden Eintrag prüfen und ggf. ersetzen
    cursor.execute("SELECT kennzeichen FROM fahrzeuge WHERE kennzeichen LIKE ?", (f"%{rohwert}%",))
    bestehend = cursor.fetchone()

    if bestehend and bestehend[0] != fahrzeug_kennung:
        cursor.execute("DELETE FROM fahrzeuge WHERE kennzeichen = ?", (str(bestehend[0]),))
        cursor.execute("INSERT INTO fahrzeuge (kennzeichen) VALUES (?)", (str(fahrzeug_kennung),))
        print(f"🔁 Fahrzeugkennung '{bestehend[0]}' wurde ersetzt durch '{fahrzeug_kennung}'.")
    elif fahrzeug_kennung not in kennungsliste:
        try:
            cursor.execute("INSERT INTO fahrzeuge (kennzeichen) VALUES (?)", (str(fahrzeug_kennung),))
            print(f"➕ Fahrzeugkennung '{fahrzeug_kennung}' hinzugefügt.")
        except sqlite3.IntegrityError:
            print(f"⚠️ Fahrzeugkennung '{fahrzeug_kennung}' konnte nicht hinzugefügt werden (bereits vorhanden).")

    kennungsliste.append(fahrzeug_kennung)

    cursor.execute("SELECT 1 FROM umsatz WHERE fahrzeug_kennung = ? AND kalenderwoche = ?",
                   (fahrzeug_kennung, row['Kalenderwoche']))
    if cursor.fetchone():
        print(f"⚠️ Eintrag für {fahrzeug_kennung} in {row['Kalenderwoche']} existiert bereits – übersprungen.")
        uebersprungene_zeilen += 1
        continue

    cursor.execute("""
        INSERT INTO umsatz (
            fahrzeug_kennung, kalenderwoche, barumsatz, bankomatumsatz,
            trinkgeld_gesamt, trinkgeld_nonbar, plattform, gesamtumsatz
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fahrzeug_kennung,
        row['Kalenderwoche'],
        float(row['Barumsatz (€)']),
        float(row['Bankomatumsatz (€)']),
        float(row['Trinkgeld gesamt (€)']),
        float(row['Trinkgeld (non-bar) (€)']),
        row['Plattform'],
        float(row['Gesamtumsatz (€)'])  # 💡 Direkt aus der CSV-Spalte
    ))
    importierte_zeilen += 1

conn.commit()
conn.close()

print(f"✅ Umsatzdaten erfolgreich importiert: {importierte_zeilen} Zeilen.")
print(f"↩︎ Übersprungene Zeilen (bereits vorhanden): {uebersprungene_zeilen}")
