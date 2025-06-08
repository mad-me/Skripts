import os
import sys
import datetime
import pandas as pd
import sqlite3
from PySide6 import QtWidgets, QtCore, QtGui
from ui_loader import lade_ui
from db_access import lade_fahrer, lade_fahrzeuge
from logic.index import setze_indexnamen, parse_kw
from logic.umsatz_uberbolt import filtere_fahrer_daten
from utils import normalize_token
from views import ResultsDialog
from utils import finde_fahrzeug_match
from custom_widgets import CustomTitleBar, CustomDialog

def main():
    app = QtWidgets.QApplication(sys.argv)

    # Zentraler Darkmode-Style – KEIN Hintergrund auf QMainWindow!
    dark_stylesheet = """
        QWidget {
            background: transparent; /* nur zentralwidget wird gefärbt! */
            color: #e0e0e0;
        }
        QLabel {
            color: #e0e0e0;
            font-size: 15pt;
        }
        QLineEdit {
            background: #292929;
            border: 2px solid #404040;
            border-radius: 10px;
            padding: 8px 14px;
            font-size: 16pt;
            color: #e0e0e0;
            qproperty-placeholderTextColor: #888;
        }
        QLineEdit:focus {
            border: 2px solid #ffd600;
            background: #222;
        }
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #444, stop:1 #222);
            color: #fff;
            border-radius: 8px;
            padding: 8px 28px;
            font-size: 15pt;
            margin-top: 14px;
        }
        QDialogButtonBox QPushButton {
            background: #444;
            color: #fff;
            border-radius: 8px;
            font-size: 15pt;
            padding: 8px 28px;
            margin-top: 14px;
        }
        QPushButton:hover, QDialogButtonBox QPushButton:hover {
            background: #ffd600;
            color: #ffffff;
        }
        QComboBox {
            qproperty-alignment: 'AlignCenter';
            min-width: 220px;
            min-height: 36px;
            font-size: 15pt;
            padding: 4px 16px;
            border-radius: 8px;
            background: transparent;
            color: #ffffff;
            border: 2px solid #404040;
        }
        QComboBox QAbstractItemView {
            qproperty-textAlignment: AlignLeft;
            background: #292929;
            color: #e0e0e0;
            font-size: 15pt;
            selection-background-color: #ffd600;
            selection-color: #222;
        }
    """
    app.setStyleSheet(dark_stylesheet)

    window = lade_ui()

    # Statusbar entfernen, damit unten kein Balken bleibt
    try:
        window.setStatusBar(None)
    except Exception:
        pass

    # Fenster ohne System-Titelbar (Frameless, Transparent)
    window.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Window)
    window.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

    # Das zentrale Widget (nur dieses bekommt runden Hintergrund und Border)
    central = window.centralWidget()
    central.setObjectName("centralwidget")
    central.setStyleSheet("""
        QWidget#centralwidget {
            background-color: #232323;
            border-radius: 26px;
            border: 2.5px solid #555;
        }
    """)

    # Layout für das zentrale Widget: margin und spacing auf 0!
    old_layout = central.layout()
    main_vbox = QtWidgets.QVBoxLayout()
    main_vbox.setContentsMargins(0, 0, 0, 0)
    main_vbox.setSpacing(0)

    # Eigene dunkle Titlebar einfügen
    titlebar = CustomTitleBar(window)
    main_vbox.addWidget(titlebar)

    # Bisherigen Inhalt übernehmen
    if old_layout:
        while old_layout.count():
            item = old_layout.takeAt(0)
            if item.widget():
                main_vbox.addWidget(item.widget())
        QtWidgets.QWidget().setLayout(old_layout)
    central.setLayout(main_vbox)

    # Widgets finden
    stack = window.findChild(QtWidgets.QStackedWidget, "stackedWidget")
    weekly_btn = window.findChild(QtWidgets.QPushButton, "weeklyButton")
    load_btn = window.findChild(QtWidgets.QPushButton, "loadButton")
    back_btn = window.findChild(QtWidgets.QPushButton, "backButton")
    combo_fz = window.findChild(QtWidgets.QComboBox, "comboFahrzeug")
    combo_drv = window.findChild(QtWidgets.QComboBox, "comboFahrer")
    combo_kw = window.findChild(QtWidgets.QComboBox, "comboKW")

    # Comboboxen befüllen
    combo_drv.clear()
    combo_drv.addItems(lade_fahrer())
    combo_fz.clear()
    combo_fz.addItems(lade_fahrzeuge())

    # KW-Combobox füllen
    today = datetime.date.today()
    current_cw = today.isocalendar()[1]
    combo_kw.addItems(["Letzte Woche", "Vorletzte Woche"])
    for kw in range(current_cw - 3, 0, -1):
        combo_kw.addItem(f"KW {kw}")

    # Button-Aktivierung
    def update_ok_enabled():
        load_btn.setEnabled(
            bool(combo_fz.currentText()) and
            bool(combo_drv.currentText()) and
            bool(combo_kw.currentText())
        )

    combo_drv.currentIndexChanged.connect(update_ok_enabled)
    combo_fz.currentIndexChanged.connect(update_ok_enabled)
    combo_kw.currentIndexChanged.connect(update_ok_enabled)

    # Seitenwechsel
    def prepare_weekly_view():
        stack.setCurrentIndex(1)
        load_btn.setEnabled(False)

    weekly_btn.clicked.connect(prepare_weekly_view)
    back_btn.clicked.connect(lambda: stack.setCurrentIndex(0))

    # Hauptladefunktion
    def load_details():
        fz = combo_fz.currentText().strip()
        fahrer = combo_drv.currentText().strip()
        kw_sel = combo_kw.currentText().strip()

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

            # Umsatzdaten Uber/Bolt
            for tabelle in ["umsatz_uber", "umsatz_bolt"]:
                if tabelle in existing_tables:
                    part_df = filtere_fahrer_daten(conn, tabelle, fahrer, target_cw)
                    df_list.append(part_df)

            # Umsatzdaten 40100 nach Fahrzeug
            if fz and "umsatz_40100" in existing_tables:
                query = """
                    SELECT *, 'umsatz_40100' AS quelle
                    FROM umsatz_40100
                    WHERE CAST(kalenderwoche AS INTEGER) = ?
                """
                df_40100 = pd.read_sql_query(query, conn, params=[target_cw])
                mask = df_40100['fahrzeug_name'].apply(lambda x: finde_fahrzeug_match(fz, x))
                df_40100 = df_40100[mask]
                df_list.append(df_40100)

            conn.close()
            df_list = [df for df in df_list if not df.empty]
            if not df_list:
                QtWidgets.QMessageBox.information(window, "Keine Daten", "Keine Einträge gefunden.")
                return

            df_gesamt = pd.concat(df_list, ignore_index=True)
            cols_fahrer_fz = [c for c in ['Driver', 'fahrzeug_name'] if c in df_gesamt.columns]
            if cols_fahrer_fz:
                df_gesamt['Fahrer/Fahrzeug'] = df_gesamt[cols_fahrer_fz].bfill(axis=1).iloc[:, 0]
                df_gesamt.drop(columns=cols_fahrer_fz, inplace=True)

            # Summenzeile berechnen
            summary = {}
            for col in df_gesamt.columns:
                if any(k in col.lower() for k in ["umsatz", "trinkgeld", "betrag"]):
                    total = pd.to_numeric(df_gesamt[col], errors='coerce').sum()
                    summary[col] = total
                else:
                    summary[col] = ""
            df_gesamt.loc["Summe"] = summary

            df_gesamt = setze_indexnamen(df_gesamt)

            # Formatieren
            df_view = df_gesamt.copy()
            for col in [c for c in df_view.columns if any(k in c.lower() for k in ["umsatz", "trinkgeld", "betrag"])]:
                df_view[col] = pd.to_numeric(df_view[col], errors="coerce").apply(
                    lambda x: f"{x:,.2f} €" if pd.notnull(x) else ""
                )

            # Dialog anzeigen
            dlg = ResultsDialog(df_gesamt, fahrer, target_cw, today.year, db_path, parent=window)
            dlg.show()

        except Exception as e:
            QtWidgets.QMessageBox.critical(window, "Fehler beim Laden", str(e))

    #Event-Handler verbinden
    load_btn.clicked.connect(load_details)
    #Fenster anzeigen
    window.show()
    #Qt-Eventloop starten
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
