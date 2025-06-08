import pandas as pd
import sys
from pathlib import Path

def aggregiere_40100_datei(dateipfad: Path):
    """
    Liest die CSV-Datei ein, aggregiert Umsätze pro Fahrzeug und Kalenderwoche und gibt das Ergebnis als DataFrame zurück.
    """
    try:
        df = pd.read_csv(dateipfad, sep=";", encoding="utf-8")
    except Exception as e:
        raise ValueError(f"❌ Fehler beim Einlesen der Datei {dateipfad.name}: {e}")

    if "Zeitpunkt" not in df.columns:
        raise ValueError(f"❌ Spalte 'Zeitpunkt' fehlt in Datei: {dateipfad.name}\n🧾 Gefundene Spalten: {df.columns.tolist()}")

    # Nur Datensätze mit gültigem Zeitpunkt und Fahrzeug
    df = df[df['Zeitpunkt'].notna() & df['Fahrzeug'].notna()]
    df['Zeitpunkt_dt'] = pd.to_datetime(df['Zeitpunkt'], format="%d.%m.%Y %H:%M", errors='coerce')
    df['KW'] = df['Zeitpunkt_dt'].dt.isocalendar().week

    # Numerische Felder bereinigen
    df['Gesamt_num'] = df['Gesamt'].str.replace(',', '.', regex=True).astype(float)
    df['Trinkgeld_num'] = df['Trinkgeld'].str.replace(',', '.', regex=True).astype(float)

    # Aggregation
    summary = []
    for (fz, kw), group in df.groupby(['Fahrzeug', 'KW']):
        bar = group.loc[group['Buchungsart'].astype(str).str.contains('Barbeleg', na=False), 'Gesamt_num'].sum()
        bankomat = group.loc[~group['Buchungsart'].astype(str).str.contains('Barbeleg', na=False), 'Gesamt_num'].sum()
        tg_nonbar = group.loc[~group['Buchungsart'].astype(str).str.contains('Barbeleg', na=False), 'Trinkgeld_num'].sum()

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
    return pd.DataFrame(summary)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Fehler: Erwartet Dateipfad als Argument.")
        sys.exit(1)

    dateipfad = Path(sys.argv[1])
    if not dateipfad.exists() or not dateipfad.is_file():
        print(f"❌ Ungültiger oder nicht vorhandener Dateipfad: {dateipfad}")
        sys.exit(1)

    try:
        df_summary = aggregiere_40100_datei(dateipfad)
        print(df_summary.head())

        # ⚠️ Jetzt wird direkt die Ursprungsdatei überschrieben
        df_summary.to_csv(dateipfad, index=False, encoding="utf-8")
        print(f"✅ Aggregierte Datei überschreibt Original: {dateipfad}")
    except Exception as e:
        print(f"❌ Fehler bei der Verarbeitung von {dateipfad.name}: {e}")
        sys.exit(1)
