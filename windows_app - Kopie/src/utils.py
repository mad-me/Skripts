import unicodedata
from typing import List, Optional
import re
import sqlite3

def ermittle_fahrername_aus_tokens(namen: list[str], db_path: str) -> Optional[str]:
    """
    Versucht, aus einer Liste von (unterschiedlich geschriebenen) Fahrernamen
    genau einen passenden Fahrer aus der Datenbank zu ermitteln.
    """
    # Tokens aus allen gelieferten Namen extrahieren
    alle_tokens = set()
    for raw_name in namen:
        normiert = normalize_token(raw_name)
        alle_tokens.update(t for t in normiert.split() if t.isalpha())

    if len(alle_tokens) < 2:
        return None  # zu wenig Information

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT vorname, nachname FROM fahrer WHERE status = 1")
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"[FEHLER] Fahrer-DB konnte nicht gelesen werden: {e}")
        return None

    for vorname, nachname in rows:
        if match_driver_tokens(list(alle_tokens), vorname, nachname):
            return f"{vorname} {nachname}"

    return None  # kein Treffer

def normalize_token(text: str) -> str:
    text = unicodedata.normalize("NFKC", text.strip().lower())
    text = re.sub(r"[^a-zäöüß ]", "", text)  # Entfernt z. B. Punkte, Bindestriche etc.
    text = re.sub(r"\s+", " ", text)         # Doppelte Leerzeichen → eins
    return text

def match_driver_tokens(tokens: list[str], vorname: str, nachname: str) -> bool:
    """
    Vergleicht Tokens mit Vor- und Nachnamen – Reihenfolgeunabhängig.
    Es müssen mindestens 2 eindeutige Tokens im Namen vorkommen.
    """
    fullname = normalize_token(f"{vorname} {nachname}")
    matched = [t for t in tokens if t in fullname]
    return len(set(matched)) >= 2  # mindestens 2 unterschiedliche Tokens gefunden

def finde_fahrer_in_db(tokens: list[str], conn: sqlite3.Connection) -> Optional[str]:
    cursor = conn.cursor()
    cursor.execute("SELECT vorname, nachname FROM fahrer")
    rows = cursor.fetchall()

    print(f"[DEBUG] Suche nach Tokens: {tokens}")

    for vorname, nachname in rows:
        fullname = normalize_token(f"{vorname} {nachname}")
        rev_fullname = normalize_token(f"{nachname} {vorname}")

        if all(tok in fullname for tok in tokens) or all(tok in rev_fullname for tok in tokens):
            print(f"[DEBUG] Match gefunden: {fullname}")
            return f"{vorname} {nachname}"

    print("[DEBUG] Kein Match gefunden")
    return None

import re

def extrahiere_ziffernfolge(text: str) -> str:
    """Entfernt alle Nicht-Ziffern aus dem Text – behält nur die Ziffernfolge."""
    return re.sub(r"\D", "", text or "")

def finde_kennzeichen_per_ziffernfolge(fahrzeug_name: str, conn) -> str:
    # 1. Extrahiere Ziffernfolge wie bisher
    ziffern = extrahiere_ziffernfolge(fahrzeug_name)
    print(f"[DEBUG] Ziffern aus '{fahrzeug_name}': {ziffern}")

    # 2. Hole alle Kennzeichen aus der DB
    cursor = conn.cursor()
    cursor.execute("SELECT kennzeichen FROM fahrzeuge")
    kennzeichen_liste = [row[0] for row in cursor.fetchall()]

    # 3. Prüfe auf exakten Ziffernmatch wie bisher
    for kennzeichen in kennzeichen_liste:
        if ziffern and ziffern in extrahiere_ziffernfolge(kennzeichen):
            print(f"[DEBUG] (Ziffern) Match: {fahrzeug_name} → {kennzeichen}")
            return kennzeichen

    # 4. Fallback: Fuzzy String Matching (z.B. falls keine Ziffern)
    # Normalisiere beides (z.B. alles klein, ohne Sonderzeichen)
    normalized_input = normalize_token(fahrzeug_name)
    for kennzeichen in kennzeichen_liste:
        normalized_kennz = normalize_token(kennzeichen)
        if normalized_input in normalized_kennz or normalized_kennz in normalized_input:
            print(f"[DEBUG] (Fuzzy) Match: {fahrzeug_name} → {kennzeichen}")
            return kennzeichen

    # 5. Noch ein Fallback: Teilstring-Vergleich, falls gar nichts hilft
    for kennzeichen in kennzeichen_liste:
        if fahrzeug_name.strip().lower() in kennzeichen.strip().lower():
            print(f"[DEBUG] (Substring) Match: {fahrzeug_name} → {kennzeichen}")
            return kennzeichen

    print(f"[INFO] Kein Kennzeichen für {fahrzeug_name} gefunden.")
    return None

def finde_fahrzeug_match(combo_fz: str, df_fz_name: str) -> bool:
    """
    Vergleicht einen Fahrzeugnamen aus der ComboBox (Kennzeichen, meist mit W...)
    mit einem Namen aus der Umsatz-Tabelle (meist ohne W).
    """
    # Normalize: Alles lower-case, Leerzeichen raus
    combo_norm = (combo_fz or "").strip().lower().replace(" ", "")
    df_norm = (df_fz_name or "").strip().lower().replace(" ", "")

    # Entferne führendes 'w' im Kennzeichen für Vergleich
    if combo_norm.startswith('w'):
        combo_norm_ohne_w = combo_norm[1:]
    else:
        combo_norm_ohne_w = combo_norm

    # Exakt ab erster Ziffer vergleichen ("w576btx" -> "576btx")
    def ab_erste_ziffer(s):
        m = re.search(r'\d.*', s)
        return m.group() if m else s

    # Matching
    if ab_erste_ziffer(combo_norm) == df_norm:
        return True
    if ab_erste_ziffer(combo_norm_ohne_w) == df_norm:
        return True
    if df_norm in combo_norm or df_norm in combo_norm_ohne_w:
        return True
    return False