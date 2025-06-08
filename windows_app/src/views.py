from PySide6 import QtWidgets, QtCore
import sqlite3
import datetime
import calendar
from models import PandasModel
import pandas as pd
from utils import normalize_token

QUELLEN_MAP = {
    "umsatz_bolt": "Bolt",
    "umsatz_uber": "Uber",
    "umsatz_40100": "Taxi",
    "umsatz_31300": "Taxi",
}

class ResultsDialog(QtWidgets.QDialog):
    def __init__(self, df, driver_name, target_cw, year, db_path, parent=None):
        super().__init__(parent)

        # Member-Variablen
        self.df_numeric = df.copy()  # Original DataFrame, numerisch!
        self.driver_name = driver_name
        self.target_cw = target_cw
        self.year = year
        self.db_path = db_path

        try:
            kw = str(self.df_numeric["kalenderwoche"].dropna().iloc[0])

            # Uber/Bolt Driver extrahieren
            driver_df = self.df_numeric[
                self.df_numeric["quelle"].isin(["umsatz_uber", "umsatz_bolt"])
            ]
            name = "?"
            if not driver_df.empty and "Fahrer/Fahrzeug" in driver_df.columns:
                detected_name = driver_df["Fahrer/Fahrzeug"].dropna().iloc[0]
                tokens = [normalize_token(t) for t in detected_name.split()]

                # Abfrage in Datenbank gegen vorname + nachname
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT vorname, nachname FROM fahrer")
                rows = cursor.fetchall()
                conn.close()

                for vorname, nachname in rows:
                    fullname = normalize_token(f"{vorname} {nachname}")
                    if all(tok in fullname for tok in tokens):
                        name = f"{vorname} {nachname}"
                        break

            # Fahrzeug extrahieren (aus 40100-Tabelle)
            fz_df = self.df_numeric[self.df_numeric["quelle"] == "umsatz_40100"]
            fz = fz_df["Fahrer/Fahrzeug"].dropna().iloc[0] if not fz_df.empty else "?"

        except Exception as e:
            print(f"[WARN] Fehler beim Titelaufbau: {e}")
            kw, name, fz = "?", "?", "?"

        self.setWindowTitle(f"KW{kw} / {name} / {fz}")



        # Layout & Widgets
        self.resize(800, 600)

        main_layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableView(self)
        main_layout.addWidget(self.table)

        # View-DataFrame erzeugen & anzeigen
        self.df_view = self.format_df_for_view(self.df_numeric)
        self.model = PandasModel(self.df_view)
        self.table.setModel(self.model)

        # Spaltenbreite und Zeilenhöhe anpassen
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        # Dynamische Höhe berechnen
        row_height = self.table.verticalHeader().defaultSectionSize()
        num_rows = self.model.rowCount()
        padding = 150  # Raum für Header, Buttons usw.
        max_height = 800  # Maximale Fensterhöhe
        calculated_height = min(padding + row_height * num_rows, max_height)

        # Dynamische Breite (optional)
        self.table.resizeColumnsToContents()
        table_width = self.table.verticalHeader().width() + sum(
            [self.table.columnWidth(i) for i in range(self.model.columnCount())]) + 50
        max_width = 1200
        calculated_width = min(table_width, max_width)

        # Fenstergröße setzen
        self.resize(calculated_width, calculated_height)

        # Footer: ProgressBar & Buttons
        footer_layout = QtWidgets.QHBoxLayout()
        self.progress = QtWidgets.QProgressBar(self)
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        footer_layout.addWidget(self.progress)
        footer_layout.addStretch()
        self.cancel_btn = QtWidgets.QPushButton("Abbrechen", self)
        footer_layout.addWidget(self.cancel_btn)
        self.calc_btn = QtWidgets.QPushButton("Abrechnung", self)
        footer_layout.addWidget(self.calc_btn)
        main_layout.addLayout(footer_layout)

        # Signale verbinden
        self.cancel_btn.clicked.connect(self.reject)
        self.calc_btn.clicked.connect(self.perform_abrechnung)

    def format_df_for_view(self, df_numeric):
        """Numerische Spalten ins €-Format bringen, Index sichtbar."""
        df_view = df_numeric.copy()

        # Index-Spalte nur einfügen, wenn sie noch nicht existiert
        if "Index" not in df_view.columns:
            df_view.insert(0, "Index", df_view.index)
        else:
            # Index-Spalte ganz nach vorne schieben
            cols = ["Index"] + [c for c in df_view.columns if c != "Index"]
            df_view = df_view[cols]

        # Währungsformat anwenden
        currency_cols = [
            col for col in df_view.columns
            if any(kw in col.lower() for kw in ["umsatz", "trinkgeld", "betrag"])
        ]
        for col in currency_cols:
            df_view[col] = pd.to_numeric(df_view[col], errors="coerce")
            df_view[col] = df_view[col].apply(
                lambda x: f"{x:,.2f} €" if pd.notnull(x) else ""
            )

        return df_view.reset_index(drop=True)

    def perform_abrechnung(self):
        import os
        self.progress.setVisible(True)
        QtWidgets.QApplication.processEvents()

        # 1. Robuste Fahrersuche
        drivername_normalized = " ".join(self.driver_name.strip().lower().split())
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tarif, garage FROM fahrer
                WHERE LOWER(TRIM(vorname)) || ' ' || LOWER(TRIM(nachname)) = ?
            """, (drivername_normalized,))
            row = cursor.fetchone()
            conn.close()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "DB-Fehler", f"{e}")
            self.progress.setVisible(False)
            return

        if not row:
            QtWidgets.QMessageBox.warning(
                self,
                "Kein Fahrer gefunden",
                f"Für '{self.driver_name}' wurde in der Tabelle 'fahrer' kein Eintrag gefunden."
            )
            self.progress.setVisible(False)
            return

        tarif, garage = row
        if tarif != "%":
            QtWidgets.QMessageBox.information(
                self,
                "Unpassender Tarif",
                f"Tarif für '{self.driver_name}' ist nicht '%'.\n"
                "Die Berechnung erfolgt nur für Tarif = '%'."
            )
            self.progress.setVisible(False)
            return

        # 2. Werte aus numerischem DataFrame holen
        try:
            sum_gesamt = float(self.df_numeric.loc["Summe", "gesamtumsatz"])
            sum_bankomat = float(self.df_numeric.loc["Summe", "bankomatumsatz"])
        except Exception:
            QtWidgets.QMessageBox.critical(
                self,
                "Parsing-Fehler",
                "Konnte 'gesamtumsatz' oder 'bankomatumsatz' aus dem DataFrame nicht parsen."
            )
            self.progress.setVisible(False)
            return

        # 3. Monatsberechnung
        try:
            dt = datetime.date.fromisocalendar(self.year, self.target_cw, 1)
            monatszahl = dt.month
        except ValueError:
            QtWidgets.QMessageBox.critical(
                self,
                "Fehler",
                f"Kalenderwoche {self.target_cw} im Jahr {self.year} ist ungültig."
            )
            self.progress.setVisible(False)
            return

        montag_count = 0
        cal = calendar.Calendar(firstweekday=0)
        for day, wd in cal.itermonthdays2(self.year, monatszahl):
            if day != 0 and wd == 0:
                montag_count += 1
        if montag_count == 0:
            QtWidgets.QMessageBox.critical(
                self,
                "Fehler",
                f"Keine Montage im Jahr {self.year}, Monat {monatszahl} gefunden."
            )
            self.progress.setVisible(False)
            return

        # 4. Abrechnung berechnen (nur mit float!)
        sum_nach = sum_gesamt - (garage / montag_count)
        result = (sum_nach / 2) - sum_bankomat

        # 5. Neue Zeile in numerisches DataFrame einfügen
        new_row = {col: "" for col in self.df_numeric.columns}
        new_row["Abrechnung"] = result
        self.df_numeric.loc["Abrechnung"] = new_row

        # 6. Anzeige-DataFrame frisch formatieren und TableView neu setzen
        self.df_view = self.format_df_for_view(self.df_numeric)
        self.model = PandasModel(self.df_view)
        self.table.setModel(self.model)

        self.progress.setVisible(False)

    # Deine _parse_currency kann ggf. entfallen, da jetzt alles direkt float bleibt.
