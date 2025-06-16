import sqlite3
import pandas as pd
import sys
from pathlib import Path
import re
import import_utils

print(import_utils.__file__)

# Stelle sicher, dass das aktuelle Verzeichnis im Suchpfad ist
sys.path.append(str(Path(__file__).parent))

# Jetzt sollte der Import klappen
from import_utils import finde_kennzeichen_per_ziffernfolge, extrahiere_ziffernfolge

# -------------------------------------------
# Skript: import_40100.py
# Funktion: Findet automatisch die Datei '40100_KW*.csv' im Verzeichnis '../data/archive'
#           relativ zum Skript, liest die Spalte 'Kalenderwoche' (z.B. 'KW21'),
#           bereinigt sie zu einer Zahl und importiert die Daten in die SQLite-Tabelle 'umsatz_40100'.
#           Vor dem Einfügen wird der Fahrzeugname gegen die Tabelle 'Fahrzeuge'
#           gematcht und das dort hinterlegte Kennzeichen verwendet.
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
    fahrzeug TEXT NOT NULL,
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
    fahrzeug,
    kalenderwoche,
    barumsatz,
    bankomatumsatz,
    gesamtumsatz,
    trinkgeld_gesamt,
    trinkgeld_nonbar
) VALUES (?, ?, ?, ?, ?, ?, ?);
"""

# Helfer: Hole Kennzeichen für einen Fahrzeugnamen
def get_kennzeichen(conn: sqlite3.Connection, fahrzeug: str) -> str | None:
    return finde_kennzeichen_per_ziffernfolge(fahrzeug, conn)

def init_db(conn: sqlite3.Connection):
    """Initialisiert die DB und erstellt die Tabelle falls nötig."""
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()

def import_csv_to_db(csv_file: Path, conn: sqlite3.Connection):
    """
    Importiert CSV in die DB, liest und bereinigt die Spalte 'Kalenderwoche'.
    Zeilen mit ungültigen KW-Werten werden übersprungen.
    Vor dem Einfügen wird der Fahrzeugname gegen die Tabelle 'Fahrzeuge' gematcht
    und das gefundene Kennzeichen verwendet, falls vorhanden.
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
        fahrzeug = row['Fahrzeug']
        kennzeichen = get_kennzeichen(conn, fahrzeug)
        if kennzeichen is None:
            print(f"Warnung: Kein Kennzeichen für '{fahrzeug}' gefunden. Verwende Namen.")
            kennzeichen = fahrzeug

        cursor.execute(
            INSERT_SQL,
            (
                kennzeichen,
                row['Kalenderwoche'],
                float(row.get('Barumsatz (€)', 0) or 0),
                float(row.get('Bankomatumsatz (€)', 0) or 0),
                float(row.get('Gesamtumsatz (€)', 0) or 0),
                float(row.get('Trinkgeld gesamt (€)', 0) or 0),
                float(row.get('Trinkgeld (non-bar) (€)', 0) or 0)
            )
        )
    conn.commit()

def parse_multi_selection(selection_str, max_len):
    """
    Wandelt eine Eingabe wie '1,2,4-6' in eine Liste von Indizes um.
    max_len = maximale erlaubte Datei-Nummer (nicht Index!).
    """
    result = set()
    for part in selection_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            try:
                start = int(start)
                end = int(end)
                if start > end or start < 1 or end > max_len:
                    continue
                result.update(range(start - 1, end))  # index-basiert
            except ValueError:
                continue
        else:
            try:
                idx = int(part)
                if 1 <= idx <= max_len:
                    result.add(idx - 1)
            except ValueError:
                continue
    return sorted(result)

def main():
    files = sorted(CSV_DIR.glob(FILE_PATTERN), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        print(f"Keine Datei gefunden: {CSV_DIR / FILE_PATTERN}")
        sys.exit(1)

    print("Bitte wählen:")
    print("1 = Automatischer Import der neuesten Datei")
    print("2 = Manuelle Auswahl von einer oder mehreren Dateien (z.B. 1,3,5-8)")
    auswahl = input("Ihre Wahl: ").strip()

    if auswahl == '1':
        csv_files = [files[0]]
    elif auswahl == '2':
        print("Verfügbare Dateien:")
        for i, f in enumerate(files, 1):
            print(f"{i}: {f.name}")
        indices = input("Nummern der Dateien wählen (z.B. 1,3,5-7): ").strip()
        chosen_indices = parse_multi_selection(indices, len(files))
        if not chosen_indices:
            print("Ungültige Eingabe. Abbruch.")
            sys.exit(1)
        csv_files = [files[i] for i in chosen_indices]
    else:
        print("Ungültige Eingabe. Abbruch.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)
        for csv_file in csv_files:
            print(f"Importiere Datei: {csv_file}")
            import_csv_to_db(csv_file, conn)
            print(f"Import erfolgreich: {csv_file.name} -> Tabelle 'umsatz_40100'")
    except Exception as e:
        print(f"Fehler beim Import: {e}")
    finally:
        conn.close()

print("Datenbankpfad:", DB_PATH)

if __name__ == '__main__':
    main()
