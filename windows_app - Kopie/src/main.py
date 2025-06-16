import os
import sys
import datetime
import pandas as pd
import sqlite3
from PySide6 import QtWidgets, QtCore

from db_access import lade_fahrer, lade_fahrzeuge
from logic.index import setze_indexnamen, parse_kw
from logic.umsatz_uberbolt import filtere_fahrer_daten
from utils import finde_fahrzeug_match
from custom_widgets import CustomTitleBar, CustomDialog
from startpage import Startseite
from db_viewer import DbDialog
from utils import center_window
from indexseite import erstelle_indexseite
from abrechnungsseite import AbrechnungsSeite
from views import ResultsDialog
from monatsberichtseite import MonatsberichtSeite
from logic.WochenberichtDialog import WochenberichtDialog

APP_STYLESHEET = """
QWidget {
    background: transparent;
    color: #ececec;
    font-family: 'SF Pro Display', 'Segoe UI', 'Arial', sans-serif;
}
QWidget#centralwidget, QWidget#indexpage, QWidget#abrechnungspage {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #292929, stop:1 #232323);
    border-radius: 30px;
    box-shadow: 0 6px 40px 0 rgba(10, 10, 10, 0.16);
}
QLabel {
    color: #fff;
    font-size: 20pt;
    font-weight: 600;
    letter-spacing: 0.03em;
    padding-bottom: 8px;
    padding-top: 10px;
}
QLineEdit {
    background: #232323;
    border: 2px solid #444;
    border-radius: 16px;
    padding: 12px 20px;
    font-size: 18pt;
    color: #fff;
    qproperty-placeholderTextColor: #888;
    outline: none;
    transition: border-color 0.28s;
    box-shadow: 0 4px 16px 0 rgba(40, 40, 40, 0.15);
}
QLineEdit:focus {
    border: 2.2px solid #ffd600;
    background: #181818;
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffe066, stop:1 #ffd600);
    color: #232323;
    border-radius: 18px;
    padding: 16px 44px;
    font-size: 20pt;
    font-weight: 800;
    margin-top: 20px;
    border: none;
    box-shadow: 0 4px 20px 0 rgba(255, 214, 0, 0.08);
    letter-spacing: 0.04em;
    transition: background 0.24s, color 0.18s, box-shadow 0.18s;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #fffde7, stop:1 #ffe066);
    color: #111;
    box-shadow: 0 8px 30px 0 rgba(255, 214, 0, 0.18);
}
QPushButton:pressed {
    background: #ffd600;
    color: #111;
    box-shadow: 0 2px 6px 0 rgba(255, 214, 0, 0.15);
}
QDialogButtonBox QPushButton {
    background: #fffde7;
    color: #232323;
    border-radius: 18px;
    font-size: 17pt;
    padding: 13px 40px;
    margin-top: 12px;
    font-weight: 700;
    min-width: 140px;
    min-height: 48px;
}
QComboBox {
    min-width: 250px;
    min-height: 44px;
    font-size: 17pt;
    padding: 10px 20px;
    border-radius: 16px;
    background: #1c1c1c;
    color: #fff;
    border: 2px solid #555;
    margin-bottom: 14px;
    transition: border-color 0.22s;
}
QComboBox:focus {
    border: 2.3px solid #ffd600;
    background: #222;
}
QComboBox QAbstractItemView {
    background: #222;
    color: #fff;
    border-radius: 12px;
    selection-background-color: #ffd600;
    selection-color: #232323;
    font-size: 17pt;
}
QComboBox::drop-down {
    background: transparent;
    border: none;
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 36px;
}
QComboBox::down-arrow {
    image: url(:/qt-project.org/styles/commonstyle/images/arrowdown-16.png);
    width: 22px;
    height: 22px;
    background: transparent;
}
QComboBox::down-arrow:on {
    top: 1px;
    left: 1px;
}
QScrollBar:vertical, QScrollBar:horizontal {
    background: transparent;
    border-radius: 8px;
    width: 10px;
    margin: 4px;
}
QScrollBar::handle {
    background: #ffd600;
    border-radius: 8px;
}
QScrollBar::handle:hover {
    background: #ffe066;
}
QScrollBar::add-line, QScrollBar::sub-line {
    background: none;
    border: none;
}
QWidget#customTitleBar {
    background: transparent;
    border-top-left-radius: 18px;
    border-top-right-radius: 18px;
}
"""

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)

    window = QtWidgets.QMainWindow()
    window.resize(800, 250)
    window.setWindowTitle("EL KAPTIN KG")
    window.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Window)
    window.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

    # --- Zentrale Widget-Struktur ---
    central = QtWidgets.QWidget()
    central.setObjectName("centralwidget")
    window.setCentralWidget(central)
    main_vbox = QtWidgets.QVBoxLayout(central)
    main_vbox.setContentsMargins(10, 0, 10, 10)
    main_vbox.setSpacing(0)

    # --- CustomTitleBar ---
    titlebar = CustomTitleBar(window, title_text="EL KAPTIN KG", show_back=False)
    main_vbox.addWidget(titlebar)

    stack = QtWidgets.QStackedWidget()
    main_vbox.addWidget(stack)

    # --- Stack-Index 0: Startseite ---
    start_widget = Startseite(window)
    stack.addWidget(start_widget)

    # --- Stack-Index 1: Indexseite/Menü ---
    index_widget, weekly_btn, monthly_btn, btn_db_uebersicht = erstelle_indexseite(window)
    index_widget.setObjectName("indexpage")
    stack.addWidget(index_widget)

    # --- Stack-Index 2: Monatsbericht ---
    monatsbericht_widget = MonatsberichtSeite(parent=window)
    stack.addWidget(monatsbericht_widget)

    # --- Stack-Index 3: Abrechnungsseite ---
    fahrer_liste = lade_fahrer()
    fahrzeug_liste = lade_fahrzeuge()
    today = datetime.date.today()
    current_cw = today.isocalendar()[1]
    abrechnung_widget = AbrechnungsSeite(fahrer_liste, fahrzeug_liste, current_cw, parent=window)
    abrechnung_widget.setObjectName("abrechnungspage")
    stack.addWidget(abrechnung_widget)

    # --- Stack beim Start auf Startseite ---
    stack.setCurrentWidget(start_widget)

    # ---------- Seitenwechsel ----------

    # Startseite → Indexseite (Menü)
    start_widget.btn_start.clicked.connect(lambda: stack.setCurrentWidget(index_widget))

    # Indexseite → Abrechnungsseite
    def zeige_abrechnungsseite():
        stack.setCurrentWidget(abrechnung_widget)
        titlebar.setTitle("Wöchentliche Abrechnung")
        titlebar.back_btn.setVisible(True)
        try:
            titlebar.backClicked.disconnect()
        except Exception:
            pass
        titlebar.backClicked.connect(gehe_zurueck_zu_index)

    # Indexseite → Monatsbericht
    def zeige_monatsbericht():
        stack.setCurrentWidget(monatsbericht_widget)
        window.resize(200, 200)
        titlebar.setTitle("Monatsbericht")
        titlebar.back_btn.setVisible(True)
        try:
            titlebar.backClicked.disconnect()
        except Exception:
            pass
        titlebar.backClicked.connect(gehe_zurueck_zu_index)

    def gehe_zurueck_zu_index():
        stack.setCurrentWidget(index_widget)
        titlebar.setTitle("Was möchtest du tun?")
        titlebar.back_btn.setVisible(False)

    weekly_btn.clicked.connect(zeige_abrechnungsseite)
    monthly_btn.clicked.connect(zeige_monatsbericht)

    # Datenbank-Übersicht
    btn_db_uebersicht.clicked.connect(lambda: open_db_viewer(window))

    # --- Aktivieren/Deaktivieren des Abrechnen-Buttons ---
    def update_ok_enabled():
        enabled = (bool(abrechnung_widget.combo_fz.currentText())
                   and bool(abrechnung_widget.combo_drv.currentText())
                   and bool(abrechnung_widget.combo_kw.currentText()))
        abrechnung_widget.load_btn.setEnabled(enabled)
    abrechnung_widget.combo_drv.currentIndexChanged.connect(update_ok_enabled)
    abrechnung_widget.combo_fz.currentIndexChanged.connect(update_ok_enabled)
    abrechnung_widget.combo_kw.currentIndexChanged.connect(update_ok_enabled)
    update_ok_enabled()

    # --- Abrechnen-Button ---
    def load_details():
        fz = abrechnung_widget.combo_fz.currentText().strip()
        fahrer = abrechnung_widget.combo_drv.currentText().strip()
        kw_sel = abrechnung_widget.combo_kw.currentText().strip()
        target_cw = parse_kw(kw_sel, current_cw)
        if target_cw is None:
            QtWidgets.QMessageBox.warning(window, "Ungültige Eingabe", "Kalenderwoche nicht lesbar.")
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.normpath(os.path.join(base_dir, os.pardir, os.pardir, "SQL", "EKK.db"))
        if not os.path.exists(db_path):
            QtWidgets.QMessageBox.critical(window, "Fehler", f"Datenbank nicht gefunden:\n{db_path}")
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            existing_tables = [
                row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            ]
            df_list = []

            for tabelle in ["umsatz_uber", "umsatz_bolt"]:
                if tabelle in existing_tables:
                    part_df = filtere_fahrer_daten(conn, tabelle, fahrer, target_cw)
                    df_list.append(part_df)

            if fz and "umsatz_40100" in existing_tables:
                query = """
                    SELECT *, 'umsatz_40100' AS quelle
                    FROM umsatz_40100
                    WHERE CAST(kalenderwoche AS INTEGER) = ?
                """
                df_40100 = pd.read_sql_query(query, conn, params=[target_cw])
                mask = df_40100['fahrzeug'].apply(lambda x: finde_fahrzeug_match(fz, x))
                df_40100 = df_40100[mask]
                df_list.append(df_40100)

            conn.close()
            df_list = [df for df in df_list if not df.empty]
            if not df_list:
                QtWidgets.QMessageBox.information(window, "Keine Daten", "Keine Einträge gefunden.")
                return

            df_gesamt = pd.concat(df_list, ignore_index=True)
            cols_fahrer_fz = [c for c in ['Driver', 'fahrzeug'] if c in df_gesamt.columns]
            if cols_fahrer_fz:
                df_gesamt['Fahrer/Fahrzeug'] = df_gesamt[cols_fahrer_fz].bfill(axis=1).iloc[:, 0]
                df_gesamt.drop(columns=cols_fahrer_fz, inplace=True)

            summary = {}
            for col in df_gesamt.columns:
                if any(k in col.lower() for k in ["umsatz", "trinkgeld", "betrag"]):
                    total = pd.to_numeric(df_gesamt[col], errors='coerce').sum()
                    summary[col] = total
                else:
                    summary[col] = ""
            df_gesamt.loc["Summe"] = summary

            df_gesamt = setze_indexnamen(df_gesamt)

            df_view = df_gesamt.copy()
            for col in [c for c in df_view.columns if any(k in c.lower() for k in ["umsatz", "trinkgeld", "betrag"])]:
                df_view[col] = pd.to_numeric(df_view[col], errors="coerce").apply(
                    lambda x: f"{x:,.2f} €" if pd.notnull(x) else ""
                )

            dlg = ResultsDialog(
                df_gesamt,  # DataFrame
                fahrer,  # driver_name
                abrechnung_widget.combo_fz,  # combo_fz (ComboBox, NICHT target_cw!)
                target_cw,  # target_cw (KW als int)
                today.year,  # year
                db_path,  # db_path
                parent=window
            )
            dlg.show()
            center_window(dlg)

        except Exception as e:
            QtWidgets.QMessageBox.critical(window, "Fehler beim Laden", str(e))

    abrechnung_widget.load_btn.clicked.connect(load_details)

    window.show()
    qr = window.frameGeometry()
    cp = QtWidgets.QApplication.primaryScreen().availableGeometry().center()
    qr.moveCenter(cp)
    window.move(qr.topLeft())
    sys.exit(app.exec())

def open_db_viewer(parent):
    db_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "SQL", "EKK.db"))
    dlg = DbDialog(db_path, parent=parent)
    dlg.exec()

if __name__ == "__main__":
    main()
