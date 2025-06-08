#!/usr/bin/env python3
import argparse
import re
import os
import sys
from datetime import datetime
from pathlib import Path

import sqlite3
from PyQt6.QtWidgets import QApplication, QFileDialog
from pdf2image import convert_from_path
import pytesseract

# OCR-Konfiguration
pytesseract.pytesseract.tesseract_cmd = r"C:/Users/moahm/AppData/Local/Programs/Tesseract-OCR/tesseract.exe"
POPPLER_PATH = r"C:\Users\moahm\AppData\Local\Programs\poppler-24.08.0\Library\bin"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.normpath(os.path.join(BASE_DIR, os.pardir, os.pardir, "SQL", "EKK.db"))

TITEL = [
    "dr", "mag", "dipl-ing", "dipl", "ing", "msc", "bsc", "ba", "ma",
    "prof", "univ", "med", "phil", "jur", "llm", "mba", "phd"
]

def get_name_for_dnr(conn, dnr):
    cursor = conn.cursor()
    cursor.execute("SELECT vorname, nachname FROM fahrer WHERE dienstnehmernummer = ?", (dnr,))
    res = cursor.fetchone()
    if res:
        return f"{res[0]} {res[1]}"
    return None

def clean_name(name):
    if not name:
        return ""
    name = name.lower()
    titel_pattern = r"^((" + "|".join(TITEL) + r")[\.\s]*)+"
    name = re.sub(titel_pattern, "", name)
    name = re.sub(r"[^a-zäöüß \-]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip().title()

def parse_int(val):
    match = re.search(r"\d+", str(val or ""))
    return int(match.group()) if match else None

def parse_euro(val):
    val = (val or "").replace(".", "").replace(",", ".").replace(" ", "")
    try:
        return float(val)
    except Exception:
        return 0.0

def normalize_token(text: str) -> str:
    text = re.sub(r"[^a-zäöüß ]", "", text.strip().lower())
    text = re.sub(r"\s+", " ", text)
    return text

def get_name_for_dnr(conn, dnr):
    cursor = conn.cursor()
    cursor.execute("SELECT vorname, nachname FROM fahrer WHERE dienstnehmernummer = ?", (dnr,))
    res = cursor.fetchone()
    if res:
        return f"{res[0]} {res[1]}"
    return None

def finde_fahrer_in_db(tokens: list[str], conn: sqlite3.Connection) -> str | None:
    cursor = conn.cursor()
    cursor.execute("SELECT vorname, nachname FROM fahrer")
    rows = cursor.fetchall()

    wanted = set(t.lower() for t in tokens if t.strip())
    matches = []

    for vorname, nachname in rows:
        db_tokens = set(normalize_token(f"{vorname} {nachname}").split())
        rev_db_tokens = set(normalize_token(f"{nachname} {vorname}").split())
        if wanted <= db_tokens or wanted <= rev_db_tokens:
            matches.append((vorname, nachname))

    if len(matches) == 1:
        print(f"[DEBUG] Exakter Match gefunden: {matches[0][0]} {matches[0][1]}")
        return f"{matches[0][0]} {matches[0][1]}"
    elif len(matches) > 1:
        print(f"[WARN] Mehrere mögliche Kandidaten für Tokens {tokens}: {[f'{v} {n}' for v, n in matches]}")
        return None
    else:
        print("[DEBUG] Kein Match gefunden")
        return None


def ergänze_fahrer_daten(conn, name, dnr):
    cursor = conn.cursor()
    if name and not dnr:
        tokens = [t for t in re.split(r"\s+", name.strip()) if t]
        gef_name = finde_fahrer_in_db(tokens, conn)
        if not gef_name:
            return name, None
        cursor.execute("SELECT dienstnehmernummer FROM fahrer WHERE TRIM(vorname || ' ' || nachname) = ?", (gef_name,))
        res = cursor.fetchone()
        return (gef_name, res[0]) if res else (gef_name, None)
    elif dnr and not name:
        cursor.execute("SELECT vorname, nachname FROM fahrer WHERE dienstnehmernummer = ?", (dnr,))
        res = cursor.fetchone()
        if res:
            fullname = f"{res[0]} {res[1]}"
            return (fullname, dnr)
        else:
            return (None, dnr)
    else:
        return (name, dnr)

def extract_month_year_from_filename(filename: str, keyword: str) -> tuple[int, int]:
    filename_upper = filename.upper()
    if keyword in ("FL", "ARF"):
        try:
            base = filename_upper.split(keyword)[-1]
            year_part = base[0:2]
            month_part = base[2:4]
            year = int("20" + year_part)
            month = int(month_part)
            if 1 <= month <= 12:
                return month, year
        except Exception:
            pass
    elif keyword == "ABRECHNUNGEN":
        match = re.search(r'Abrechnungen?\s+(\d{2})_(\d{4})', filename, re.IGNORECASE)
        if match:
            month = int(match.group(1))
            year = int(match.group(2))
            if 1 <= month <= 12:
                return month, year
    print("⚠️ Konnte Monat und Jahr nicht automatisch erkennen.")
    try:
        user_input = input("Bitte Monat eingeben (1–12, Enter = aktueller Monat): ").strip()
        if user_input:
            month = int(user_input)
            if not (1 <= month <= 12):
                raise ValueError
        else:
            month = datetime.now().month
        year = datetime.now().year
        return month, year
    except ValueError:
        print("❌ Ungültige Eingabe. Verwende aktuellen Monat.")
        return datetime.now().month, datetime.now().year

def choose_multiple_files_gui() -> list[Path]:
    downloads_path = Path.home() / "Downloads"
    if not downloads_path.exists():
        downloads_path = Path.home()
    app = QApplication(sys.argv)
    dialog = QFileDialog()
    dialog.setWindowTitle("Bitte PDF-Dateien auswählen")
    dialog.setDirectory(str(downloads_path))
    dialog.setNameFilter("PDF-Dateien (*.pdf)")
    dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
    if dialog.exec():
        return [Path(f) for f in dialog.selectedFiles()]
    return []

def process_abrechnung(pdf_path: Path, db_path: Path):
    images = convert_from_path(str(pdf_path), dpi=300, poppler_path=POPPLER_PATH)
    patterns = {
        'Dienstnehmer': r'Dienstnehmer\W*[:\-]?\s*(.*?)\s*(?=DN[- ]?Nr)',
        'DN-Nr.': r'DN[- ]?Nr\.?\W*[:\-]?\s*(\d+)',
        'Brutto': r'Brutto\W*[:\-]?\s*(\d+[\d\.,]*)',
        'Zahlbetrag': r'Zahlbetrag\W*[:\-]?\s*(\d+[\d\.,]*)'
    }
    flags = re.IGNORECASE | re.DOTALL

    payroll_rows = []
    for img in images:
        text6 = pytesseract.image_to_string(img, lang='deu', config='--psm 6')
        text11 = None
        row = {}
        for key, pat in patterns.items():
            m6 = re.search(pat, text6, flags)
            if m6:
                row[key] = m6.group(1).strip()
            else:
                if text11 is None:
                    text11 = pytesseract.image_to_string(img, lang='deu', config='--psm 11')
                m11 = re.search(pat, text11, flags)
                row[key] = m11.group(1).strip() if m11 else ''
        payroll_rows.append(row)

    month, year = extract_month_year_from_filename(pdf_path.name, "ABRECHNUNGEN")
    monat_jahr = f"{month:02d}/{str(year)[2:]}"  # "05/25"

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Spalte monat_jahr ergänzen, falls sie nicht existiert
    try:
        cursor.execute("ALTER TABLE gehalt ADD COLUMN monat_jahr TEXT")
    except sqlite3.OperationalError:
        pass

    # UNIQUE-Index für dienstnehmer, dienstnehmernummer, monat_jahr
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS unique_gehalt 
        ON gehalt (dienstnehmer, dienstnehmernummer, monat_jahr)
    """)

    for row in payroll_rows:
        dnr = parse_int(row.get("DN-Nr.", ""))
        if dnr:
            name = get_name_for_dnr(conn, dnr)
            if not name:
                print(f"❌ Konnte für DN-Nr. {dnr} keinen Namen zuordnen!")
                continue
        else:
            raw_name = clean_name(row.get("Dienstnehmer", ""))
            if not raw_name:
                print(f"❌ Kein gültiger Datensatz in Zeile: {row}")
                continue
            tokens = [t for t in re.split(r"\s+", raw_name.strip()) if t]
            matched_name = finde_fahrer_in_db(tokens, conn)
            if matched_name:
                name = matched_name
                cursor = conn.cursor()
                cursor.execute("SELECT dienstnehmernummer FROM fahrer WHERE TRIM(vorname || ' ' || nachname) = ?",
                               (matched_name,))
                res = cursor.fetchone()
                dnr = res[0] if res else None
            else:
                name = raw_name
                dnr = None

        if not name or not dnr:
            print(f"❌ Kein gültiger Datensatz in Zeile: {row}")
            continue

        cursor.execute("""
            INSERT OR REPLACE INTO gehalt 
            (dienstnehmer, dienstnehmernummer, brutto, netto, monat_jahr)
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            dnr,
            parse_euro(row.get("Brutto", "0")),
            parse_euro(row.get("Zahlbetrag", "0")),
            monat_jahr
        ))

    conn.commit()
    conn.close()
    print(f"✅ Gehaltsabrechnung in DB importiert ({len(payroll_rows)} Zeilen)")

    pdf_target_dir = pdf_path.parent / "importiert"
    pdf_target_dir.mkdir(exist_ok=True)

    try:
        pdf_path.replace(pdf_target_dir / pdf_path.name)
        print(f"📁 PDF verschoben nach: {pdf_target_dir / pdf_path.name}")
    except Exception as e:
        print(f"⚠️ Konnte PDF nicht verschieben: {e}")

def get_kennzeichen_for_kennung(conn, kennung):
    cursor = conn.cursor()
    cursor.execute("SELECT verkehrskennzeichen FROM zuordnung_40100 WHERE kennung = ?", (kennung,))
    res = cursor.fetchone()
    if res:
        return res[0]
    return None

def process_arf(pdf_path: Path, db_path: Path):
    images = convert_from_path(str(pdf_path), dpi=300, poppler_path=POPPLER_PATH)
    arf_rows = []

    for img in images:
        text = pytesseract.image_to_string(img, lang='deu', config='--psm 6')
        print("------ OCR-TEXT ------")
        print(text)
        print("------ ENDE OCR-TEXT ------")

        # 1. Blockweise parsen: Finde alle Fahrzeug-Blöcke
        blocks = re.split(r"Fahrzeug:\s*(\d+)\s*([A-Z ]+)", text)
        # Der erste Block ist vor dem ersten Fahrzeug, also überspringen
        for i in range(1, len(blocks), 3):
            kennung = blocks[i]
            kennzeichen_ocr = blocks[i+1].strip().replace(" ", "")
            blocktext = blocks[i+2]

            # Finde echtes Kennzeichen per Kennung
            conn = sqlite3.connect(str(db_path))
            kennzeichen = get_kennzeichen_for_kennung(conn, int(kennung)) if kennung else None
            conn.close()
            if not kennzeichen:
                kennzeichen = kennzeichen_ocr  # zur Not das OCR-Kennzeichen verwenden

            # 2. Zeilen im Block extrahieren, die mit Betrag enden ("... 240,00 20,00 288,00")
            lines = blocktext.splitlines()
            for line in lines:
                # Ignoriere Überschriften/Gesamtzeilen
                if not re.search(r"\d+,\d+\s+\d+,\d+$", line):
                    continue
                # Extrahiere alle Beträge von rechts
                betraege = re.findall(r"(\d+,\d+)", line)
                if len(betraege) >= 2:
                    netto = betraege[-2]
                    brutto = betraege[-1]
                    arf_rows.append({
                        "Kennung": kennung,
                        "Verkehrskennzeichen": kennzeichen,
                        "Netto": netto,
                        "Brutto": brutto
                    })

    month, year = extract_month_year_from_filename(pdf_path.name, "ARF")
    monat_jahr = f"{month:02d}/{str(year)[2:]}"  # "05/25"

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE funk_40100 ADD COLUMN monat_jahr TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS unique_funk_40100 
        ON funk_40100 (verkehrskennzeichen, kennung, monat_jahr)
    """)

    for row in arf_rows:
        kennung = parse_int(row.get("Kennung", ""))
        kennzeichen = row.get("Verkehrskennzeichen")
        netto = parse_euro(row.get("Netto", "0"))
        brutto = parse_euro(row.get("Brutto", "0"))

        if not kennzeichen or not kennung:
            print(f"❌ Kein gültiger Datensatz in Zeile: {row}")
            continue

        cursor.execute("""
            INSERT OR REPLACE INTO funk_40100
            (verkehrskennzeichen, kennung, netto, brutto, monat_jahr)
            VALUES (?, ?, ?, ?, ?)
        """, (
            kennzeichen,
            kennung,
            netto,
            brutto,
            monat_jahr
        ))

    conn.commit()
    conn.close()
    print(f"✅ ARF in DB importiert ({len(arf_rows)} Zeilen)")

    pdf_target_dir = pdf_path.parent / "importiert"
    pdf_target_dir.mkdir(exist_ok=True)
    try:
        pdf_path.replace(pdf_target_dir / pdf_path.name)
        print(f"📁 PDF verschoben nach: {pdf_target_dir / pdf_path.name}")
    except Exception as e:
        print(f"⚠️ Konnte PDF nicht verschieben: {e}")


def detect_processor(pdf_name: str):
    name_upper = pdf_name.upper()
    if "ABRECHNUNGEN" in name_upper:
        return process_abrechnung, "ABRECHNUNGEN"
    elif "ARF" in name_upper:
        return process_arf, "ARF"
    else:
        return None, None

def main():
    parser = argparse.ArgumentParser(description="PDF-Verarbeitung für Gehaltsabrechnung (Import in DB, mit Abgleich und Bereinigung).")
    parser.add_argument("pdf_path", nargs='?', type=Path, help="Pfad zur PDF-Datei (optional)")
    parser.add_argument("-d", "--db-path", type=Path, default=DB_PATH, help="Pfad zur SQLite-DB")

    args = parser.parse_args()

    if args.pdf_path is None:
        print("📂 Kein Pfad angegeben – öffne Dateiauswahldialog...")
        selected_files = choose_multiple_files_gui()
        if not selected_files:
            print("❌ Keine Dateien ausgewählt. Abbruch.")
            exit(1)
    else:
        selected_files = [args.pdf_path.expanduser().resolve()]

    db_path = args.db_path.expanduser().resolve()

    for pdf_path in selected_files:
        if not pdf_path.is_file():
            print(f"⚠️ Datei nicht gefunden: {pdf_path}")
            continue

        proc_func, key = detect_processor(pdf_path.name)
        if not proc_func:
            print(f"⚠️ Kein gültiges Schlüsselwort in {pdf_path.name}")
            continue

        try:
            proc_func(pdf_path, db_path)
        except Exception as e:
            print(f"❌ Fehler bei Datei {pdf_path.name}: {e}")

    print("✅ Verarbeitung abgeschlossen.")

if __name__ == "__main__":
    main()
