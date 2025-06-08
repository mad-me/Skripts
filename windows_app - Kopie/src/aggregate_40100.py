import pandas as pd
from datetime import datetime
import os
import glob
import subprocess


def finde_neueste_40100_datei(download_ordner):
    pattern = os.path.join(download_ordner, "UPORTAL_GETUMSATZLISTE_*.csv")
    dateien = glob.glob(pattern)
    if not dateien:
        raise FileNotFoundError("Keine passende 40100-CSV-Datei gefunden.")
    return max(dateien, key=os.path.getctime)


def aggregiere_40100_datei(dateipfad=None, download_ordner=None):
    if dateipfad is None:
        if download_ordner is None:
            download_ordner = os.path.join(os.path.expanduser("~"), "Downloads")
        dateipfad = finde_neueste_40100_datei(download_ordner)

    df = pd.read_csv(dateipfad, sep=";", encoding="utf-8")

    # Nur gültige Zeitstempel und Fahrzeuge
    df = df[df['Zeitpunkt'].notna() & df['Fahrzeug'].notna()]
    df['Zeitpunkt_dt'] = pd.to_datetime(df['Zeitpunkt'], format="%d.%m.%Y %H:%M", errors='coerce')
    df['KW'] = df['Zeitpunkt_dt'].dt.isocalendar().week

    # Beträge bereinigen
    df['Gesamt_num'] = df['Gesamt'].replace(',', '.', regex=True).astype(float)
    df['Trinkgeld_num'] = df['Trinkgeld'].replace(',', '.', regex=True).astype(float)

    # Gruppierung und Aggregation
    summary = []
    for (fz, kw), group in df.groupby(['Fahrzeug', 'KW']):
        bar = group[group['Buchungsart'] == 'Barbeleg']['Gesamt_num'].sum()
        bankomat = group[group['Buchungsart'] != 'Barbeleg']['Gesamt_num'].sum()
        gesamtumsatz = group['Gesamt_num'].sum()
        tg_total = group['Trinkgeld_num'].sum()
        tg_nonbar = group[group['Buchungsart'] != 'Barbeleg']['Trinkgeld_num'].sum()

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

    df_summary = pd.DataFrame(summary)
    return df_summary


if __name__ == "__main__":
    df = aggregiere_40100_datei()
    print(df.head())  # Optional: Vorschau im Terminal

    # Datei speichern für Folgeimport
    df.to_csv("40100_aggregierte_umsätze_pro_fahrzeug.csv", index=False, encoding="utf-8")

    # Nachgelagertes Skript starten
    subprocess.run(["python", "import_fahrer_from_json.py"])

