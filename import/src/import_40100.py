#!/usr/bin/env python3
import sqlite3
import pandas as pd
import sys
from pathlib import Path

# -------------------------------------------
# Skript: import_40100.py
# Funktion: Findet automatisch die Datei '40100_KW*.csv' im Verzeichnis '../data/archive'
#           relativ zum Skript, liest die Spalte 'Kalenderwoche' (z.B. 'KW21'),
#           bereinigt sie zu einer Zahl und importiert die Daten in die SQLite-Tabelle 'umsatz_40100'.
# -------------------------------------------

# --- Konfiguration ---
DB_PATH = (Path(__file__).parent / ".." / ".." / "SQL" / "EKK.db").resolve()

# CSV-Verzeichnis relativ zum Skript
SCRIPT_DIR = Path(__file__).parent
CSV_DIR = (SCRIPT_DIR / ".." / "data" / "archive").resolve()
FILE_PATTERN = "40100_KW*.csv"

# SQL-Befehle
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS umsatz_40100 (
    fahrzeug_name TEXT NOT NULL,
    kalenderwoche INTEGER NOT NULL,
    barumsatz REAL,
    bankomatumsatz REAL,
    gesamtumsatz REAL,
    trinkgeld_gesamt REAL,
    trinkgeld_nonbar REAL
);
"""

INSERT_SQL = """
INSERT INTO umsatz_40100 (
    fahrzeug_name,
    kalenderwoche,
    barumsatz,
    bankomatumsatz,
    gesamtumsatz,
    trinkgeld_gesamt,
    trinkgeld_nonbar
) VALUES (?, ?, ?, ?, ?, ?, ?);
"""

def init_db(conn: sqlite3.Connection):
    """Initialisiert die DB und erstellt die Tabelle falls nötig."""
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()


def import_csv_to_db(csv_file: Path, conn: sqlite3.Connection):
    """
    Importiert CSV in die DB, liest und bereinigt die Spalte 'Kalenderwoche'.
    Zeilen mit ungültigen KW-Werten werden übersprungen.
    """
    # Einlesen mit Semikolon
    df = pd.read_csv(csv_file, sep=';', encoding='utf-8')
    # Fallback auf Komma-Delimiter
    if len(df.columns) == 1:
        df = pd.read_csv(csv_file, sep=',', encoding='utf-8')

    df.columns = df.columns.str.strip()

    if 'Kalenderwoche' not in df.columns:
        raise KeyError(f"Spalte 'Kalenderwoche' nicht gefunden. Gefundene Spalten: {df.columns.tolist()}")

    # Bereinigen: Entfernt alle Nicht-Ziffern und wandelt in int um
    df['Kalenderwoche_raw'] = df['Kalenderwoche'].astype(str)
    df['Kalenderwoche'] = (
        df['Kalenderwoche_raw']
        .str.extract(r"(\d+)")[0]
        .astype(float, errors='ignore')  # float intermediate
        .fillna(0)
        .astype(int)
    )

    # Zeilen ohne valide Zahl löschen
    invalid = df[df['Kalenderwoche'] == 0].shape[0]
    if invalid:
        print(f"Warnung: {invalid} Zeilen mit ungültiger Kalenderwoche übersprungen.")
    df = df[df['Kalenderwoche'] > 0]

    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute(
            INSERT_SQL,
            (
                row['Fahrzeug'],
                row['Kalenderwoche'],
                float(row.get('Barumsatz (€)', 0) or 0),
                float(row.get('Bankomatumsatz (€)', 0) or 0),
                float(row.get('Gesamtumsatz (€)', 0) or 0),
                float(row.get('Trinkgeld gesamt (€)', 0) or 0),
                float(row.get('Trinkgeld (non-bar) (€)', 0) or 0)
            )
        )
    conn.commit()


def main():
    # Auto-Find der CSV
    files = list(CSV_DIR.glob(FILE_PATTERN))
    if not files:
        print(f"Keine Datei gefunden: {CSV_DIR / FILE_PATTERN}")
        sys.exit(1)

    csv_file = max(files, key=lambda f: f.stat().st_mtime)
    print(f"Importiere Datei (zuletzt geändert): {csv_file}")

    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)
        import_csv_to_db(csv_file, conn)
        print(f"Import erfolgreich: {csv_file.name} -> Tabelle 'umsatz_40100'")
    except Exception as e:
        print(f"Fehler beim Import: {e}")
    finally:
        conn.close()

print("Datenbankpfad:", DB_PATH)

if __name__ == '__main__':
    main()
