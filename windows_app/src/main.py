import os
import sys
import datetime
import re
import pandas as pd
import sqlite3
from PySide6 import QtWidgets, QtCore, QtUiTools

from utils import normalize_token, filtere_fahrer_daten
from views import ResultsDialog

# -----------------------------------------------------------
# GLOBALE KONSTANTEN & MAPS
# -----------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.normpath(os.path.join(BASE_DIR, os.pardir, os.pardir, "SQL", "EKK.db"))
UI_PATH = os.path.normpath(os.path.join(BASE_DIR, os.pardir, "ui", "mainwindow.ui"))

QUELLEN_MAP = {
    "umsatz_bolt": "Bolt",
    "umsatz_uber": "Uber",
    "umsatz_40100": "Taxi",
    "umsatz_31300": "Taxi",
}

# -----------------------------------------------------------
# HILFSFUNKTIONEN
# -----------------------------------------------------------

def setze_indexnamen(df):
    df = df.copy()
    indexnamen = []
    for idx, row in df.iterrows():
        if str(idx) in ["Summe", "Abrechnung"]:
            indexnamen.append(str(idx))
        elif "quelle" in df.columns and row["quelle"] in QUELLEN_MAP:
            indexnamen.append(QUELLEN_MAP[row["quelle"]])
        else:
            indexnamen.append(str(idx))
    df["Index"] = indexnamen
    return df

def lade_ui():
    loader = QtUiTools.QUiLoader()
    ui_file = QtCore.QFile(UI_PATH)
    if not ui_file.open(QtCore.QFile.ReadOnly):
        QtWidgets.QMessageBox.critical(None, "Fehler", f"UI-Datei nicht gefunden:\n{UI_PATH}")
        sys.exit(1)
    window = loader.load(ui_file, None)
    ui_file.close()
    if window is None:
        QtWidgets.QMessageBox.critical(None, "Fehler", "Konnte Fenster nicht erzeugen.")
        sys.exit(1)
    return window

def lade_fahrer(combo):
    combo.clear()
    if not os.path.exists(DB_PATH):
        print("[ERROR] Datenbankpfad existiert nicht:", DB_PATH)
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT vorname, nachname FROM fahrer WHERE status = 1 ORDER BY vorname, nachname")
        rows = cursor.fetchall()
        combo.addItems([f"{v} {n}" for v, n in rows])
        conn.close()
    except Exception as e:
        print("[ERROR] Fahrer-Laden fehlgeschlagen:", e)

def lade_fahrzeuge(combo):
    combo.clear()
    if not os.path.exists(DB_PATH):
        print("[ERROR] Datenbankpfad existiert nicht:", DB_PATH)
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT kennzeichen FROM fahrzeuge ORDER BY kennzeichen")
        rows = cursor.fetchall()
        combo.addItems([row[0] for row in rows])
        conn.close()
    except Exception as e:
        print("[ERROR] Fahrzeug-Laden fehlgeschlagen:", e)

def befülle_kw_combo(combo):
    today = datetime.date.today()
    current_cw = today.isocalendar()[1]
    combo.addItem("Letzte Woche")
    combo.addItem("Vorletzte Woche")
    for kw in range(max(current_cw - 3, 1), 0, -1):
        combo.addItem(f"KW {kw}")
    return current_cw

def parse_kw(combo_text, current_cw):
    if combo_text == "Letzte Woche":
        return current_cw - 1
    elif combo_text == "Vorletzte Woche":
        return current_cw - 2
    else:
        match = re.search(r"\d+", combo_text)
        return int(match.group()) if match else None

# -----------------------------------------------------------
# DATENLADEN UND DIALOGLOGIK
# -----------------------------------------------------------

def load_details(window, combo_fz, combo_drv, combo_kw, current_cw):
    fz = combo_fz.currentText().strip()
    fahrer = combo_drv.currentText().strip()
    kw_sel = combo_kw.currentText().strip()

    target_cw = parse_kw(kw_sel, current_cw)
    if not target_cw:
        QtWidgets.QMessageBox.warning(window, "Ungültige Eingabe", "Kalenderwoche nicht lesbar.")
        return

    if not os.path.exists(DB_PATH):
        QtWidgets.QMessageBox.critical(window, "Fehler", f"Datenbank nicht gefunden:\n{DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        existing_tables = [
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        ]
        df_list = []

        # Umsatz aus Uber & Bolt (Fahrer)
        if fahrer:
            for tabelle in ["umsatz_uber", "umsatz_bolt"]:
                if tabelle in existing_tables:
                    part_df = filtere_fahrer_daten(conn, tabelle, fahrer, target_cw)
                    df_list.append(part_df)

        # Umsatz aus 40100 (Fahrzeug)
        if fz and "umsatz_40100" in existing_tables:
            nummer_match = re.search(r"\d+", fz)
            nummer = nummer_match.group(0) if nummer_match else fz.strip()
            query = """
                SELECT *, 'umsatz_40100' AS quelle
                FROM umsatz_40100
                WHERE CAST(kalenderwoche AS INTEGER) = ?
                  AND TRIM(LOWER(fahrzeug_name)) = ?
            """
            params = [target_cw, nummer.strip().lower()]
            part_df = pd.read_sql_query(query, conn, params=params)
            df_list.append(part_df)

        conn.close()

        # Leere raus, zusammenführen
        df_list = [df for df in df_list if not df.empty]
        df_gesamt = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

        if df_gesamt.empty:
            QtWidgets.QMessageBox.information(window, "Keine Daten", "Keine Einträge für die Auswahl gefunden.")
            return

        # Fahrer/Fahrzeug-Spalte generieren
        cols = [c for c in ['Driver', 'fahrzeug_name'] if c in df_gesamt.columns]
        if cols:
            df_gesamt['Fahrer/Fahrzeug'] = df_gesamt[cols].bfill(axis=1).iloc[:, 0]
            df_gesamt.drop(columns=cols, inplace=True)

        # Summenzeile
        summary = {}
        for col in df_gesamt.columns:
            if any(kw in col.lower() for kw in ["umsatz", "trinkgeld", "betrag"]):
                total = pd.to_numeric(df_gesamt[col], errors="coerce").sum()
                summary[col] = total
            else:
                summary[col] = ""
        df_gesamt.loc["Summe"] = summary

        df_gesamt = setze_indexnamen(df_gesamt)

        # Formatierung für Anzeige
        df_view = df_gesamt.copy()
        currency_cols = [
            col for col in df_gesamt.columns
            if any(kw in col.lower() for kw in ["umsatz", "trinkgeld", "betrag"])
        ]
        for col in currency_cols:
            df_view[col] = pd.to_numeric(df_view[col], errors="coerce")
            df_view[col] = df_view[col].apply(lambda x: f"{x:,.2f} €" if pd.notnull(x) else "")

        # Dialog anzeigen
        dlg = ResultsDialog(
            df_gesamt,
            fahrer,
            target_cw,
            datetime.date.today().year,
            DB_PATH,
            parent=window
        )
        dlg.exec()

    except Exception as e:
        QtWidgets.QMessageBox.critical(window, "Fehler beim Laden", str(e))

# -----------------------------------------------------------
# HAUPTEINSTIEGSPUNKT
# -----------------------------------------------------------

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = lade_ui()

    # Widgets
    combo_fz = window.findChild(QtWidgets.QComboBox, "comboFahrzeug")
    combo_drv = window.findChild(QtWidgets.QComboBox, "comboFahrer")
    combo_kw = window.findChild(QtWidgets.QComboBox, "comboKW")
    stack = window.findChild(QtWidgets.QStackedWidget, "stackedWidget")
    back_btn = window.findChild(QtWidgets.QPushButton, "backButton")
    weekly_btn = window.findChild(QtWidgets.QPushButton, "weeklyButton")
    load_btn = window.findChild(QtWidgets.QPushButton, "loadButton")

    # Initialisieren
    lade_fahrer(combo_drv)
    lade_fahrzeuge(combo_fz)
    current_cw = befülle_kw_combo(combo_kw)

    load_btn.setEnabled(False)

    def update_ok_enabled():
        load_btn.setEnabled(
            bool(combo_fz.currentText()) and
            bool(combo_drv.currentText()) and
            bool(combo_kw.currentText())
        )

    def prepare_weekly_view():
        stack.setCurrentIndex(1)
        load_btn.setEnabled(False)

    weekly_btn.clicked.connect(prepare_weekly_view)
    back_btn.clicked.connect(lambda: stack.setCurrentIndex(0))
    combo_drv.currentIndexChanged.connect(update_ok_enabled)
    combo_fz.currentIndexChanged.connect(update_ok_enabled)
    combo_kw.currentIndexChanged.connect(update_ok_enabled)
    load_btn.clicked.connect(lambda: load_details(window, combo_fz, combo_drv, combo_kw, current_cw))

    # Timer für tägliches Fahrzeug-Refresh
    timer = QtCore.QTimer(window)
    timer.timeout.connect(lambda: lade_fahrzeuge(combo_fz))
    timer.start(24 * 3600 * 1000)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
