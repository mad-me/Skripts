import pandas as pd
import sys
from pathlib import Path
import re

# Für Dateiauswahldialog
import tkinter as tk
from tkinter import filedialog

def aggregiere_40100_datei(dateipfad: Path):
    try:
        df = pd.read_csv(dateipfad, sep=";", encoding="utf-8")
    except Exception as e:
        raise ValueError(f"❌ Fehler beim Einlesen der Datei {dateipfad.name}: {e}")

    if "Zeitpunkt" not in df.columns:
        raise ValueError(f"❌ Spalte 'Zeitpunkt' fehlt in Datei: {dateipfad.name}\n🧾 Gefundene Spalten: {df.columns.tolist()}")

    # Nur Datensätze mit gültigem Zeitpunkt und Fahrzeug
    df = df[df['Zeitpunkt'].notna() & df['Fahrzeug'].notna()]
    if df.empty:
        print("⚠️ Keine gültigen Daten nach Filter 'Zeitpunkt' & 'Fahrzeug'.")
        return pd.DataFrame()

    df['Zeitpunkt_dt'] = pd.to_datetime(df['Zeitpunkt'], format="%d.%m.%Y %H:%M", errors='coerce')
    df['KW'] = df['Zeitpunkt_dt'].dt.isocalendar().week

    # Numerische Felder bereinigen
    df['Gesamt_num'] = df['Gesamt'].str.replace(',', '.', regex=True).astype(float)
    df['Trinkgeld_num'] = df['Trinkgeld'].str.replace(',', '.', regex=True).astype(float)

    # Filter: Nur Einzelzeilen mit plausiblem Gesamtwert (-200 bis 200)
    df = df[(df['Gesamt_num'] >= -200) & (df['Gesamt_num'] <= 200)]
    if df.empty:
        print("⚠️ Nach Filter 'Gesamt_num' keine gültigen Buchungen übrig.")
        return pd.DataFrame()

    # Aggregation
    summary = []
    for (fz, kw), group in df.groupby(['Fahrzeug', 'KW']):
        bar = group.loc[group['Buchungsart'].astype(str).str.contains('Barbeleg', na=False), 'Gesamt_num'].sum()
        bankomat = group.loc[~group['Buchungsart'].astype(str).str.contains('Barbeleg', na=False), 'Gesamt_num'].sum()
        tg_total = group['Trinkgeld_num'].sum()
        tg_nonbar = group.loc[group['Buchungsart'] != 'Barbeleg', 'Trinkgeld_num'].sum()
        gesamtumsatz = group['Gesamt_num'].sum()

        summary.append({
            'Fahrzeug': fz,
            'Kalenderwoche': f"KW{kw:02d}",
            'Barumsatz (€)': round(bar, 2),
            'Bankomatumsatz (€)': round(bankomat, 2),
            'Gesamtumsatz (€)': round(gesamtumsatz, 2),
            'Trinkgeld gesamt (€)': round(tg_total, 2),
            'Trinkgeld (non-bar) (€)': round(tg_nonbar, 2),
            'Plattform': '40100'
        })

    summary_df = pd.DataFrame(summary)
    if summary_df.empty:
        print("⚠️ Nach Aggregation keine Daten vorhanden.")
    return summary_df


if __name__ == "__main__":
    # Dateiauswahl, falls kein Argument
    if len(sys.argv) < 2:
        print("ℹ️ Kein Dateipfad übergeben – öffne Dateiauswahldialog.")
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="40100 CSV auswählen",
            filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")]
        )
        if not file_path:
            print("❌ Kein Datei ausgewählt. Beende.")
            sys.exit(1)
        dateipfad = Path(file_path)
    else:
        dateipfad = Path(sys.argv[1])
        if not dateipfad.exists() or not dateipfad.is_file():
            print(f"❌ Ungültiger oder nicht vorhandener Dateipfad: {dateipfad}")
            sys.exit(1)

    try:
        df_summary = aggregiere_40100_datei(dateipfad)
        print(df_summary.head())

        # Speichere nur, wenn es auch Zeilen gibt
        if df_summary is not None and not df_summary.empty:
            df_summary.to_csv(dateipfad, index=False, encoding="utf-8")
            print(f"✅ Aggregierte Datei überschreibt Original: {dateipfad}")
        else:
            print("⚠️ Keine Daten zum Speichern vorhanden.")

    except Exception as e:
        print(f"❌ Fehler bei der Verarbeitung von {dateipfad.name}: {e}")
        sys.exit(1)
