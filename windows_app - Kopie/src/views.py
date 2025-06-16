from PySide6 import QtWidgets, QtCore
import sqlite3
import datetime
import calendar
import pandas as pd
from logic.WochenberichtDialog import WochenberichtDialog
from custom_widgets import CustomDialog
from utils import center_window

QUELLEN_MAP = {
    "umsatz_bolt": "Bolt",
    "umsatz_uber": "Uber",
    "umsatz_40100": "Taxi",
    "umsatz_31300": "Taxi",
}

class ResultsDialog(CustomDialog):
    def __init__(self, df, driver_name, combo_fz, target_cw, year, db_path, parent=None, ):
        super().__init__(parent=parent)

        # Member-Variablen
        self.combo_fz = combo_fz
        self.df_numeric = df.copy()
        self.driver_name = driver_name
        self.target_cw = target_cw
        self.year = year
        self.db_path = db_path
        if self.combo_fz:
            for i in range(self.combo_fz.count()):
                print(f"[DEBUG] ComboBox Item {i}: {self.combo_fz.itemText(i)}")

        # Fenstertitel
        try:
            kw = str(df["kalenderwoche"].dropna().iloc[0])
        except Exception:
            kw = "?"
        self.setWindowTitle(f"KW{kw} / {driver_name}")

        # Layout
        self.resize(800, 315)
        content_layout = QtWidgets.QVBoxLayout(self.content)

        self.df_view = self.format_df_for_view(self.df_numeric)
        grid = QtWidgets.QGridLayout()

        # Spaltenüberschriften (außer Index mit "")
        headers = list(self.df_view.columns)
        headers[0] = ""  # Index-Spalte ohne Überschrift

        # Opt. Breite für Index-Spalte bestimmen
        max_index_width = max([len(str(x)) for x in self.df_view['Index']]) * 13 + 30

        for col, name in enumerate(headers):
            header_lbl = QtWidgets.QLabel(str(name))
            header_lbl.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            header_lbl.setStyleSheet("font-size: 15pt; font-weight: bold; color: #ffffff; border: none;")
            grid.addWidget(header_lbl, 0, col)
            if col == 0:
                header_lbl.setFixedWidth(max_index_width)

        # Alle Zeilen des DataFrames anzeigen
        for row in range(len(self.df_view)):
            is_summe = str(self.df_view.iloc[row, 0]).lower() == "summe"
            for col, name in enumerate(self.df_view.columns):
                val = self.df_view.iloc[row, col]
                cell_lbl = QtWidgets.QLabel(str(val))
                # Index-Spalte immer rechtsbündig und fett
                if col == 0:
                    align = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                    style = "font-size: 15pt; font-weight: bold; color: #ffffff; border: none;"
                    cell_lbl.setFixedWidth(max_index_width)
                # Summenzeile: fett, linksbündig (außer Index-Spalte)
                elif is_summe:
                    align = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
                    style = "font-size: 15pt; font-weight: bold; color: #ffd600; border: none;"
                # Alle anderen Zellen: linksbündig
                else:
                    align = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
                    style = "font-size: 15pt; border: none;"
                cell_lbl.setAlignment(align)
                cell_lbl.setStyleSheet(style)
                grid.addWidget(cell_lbl, row + 1, col)

        content_layout.addLayout(grid)

        # Footer: ProgressBar & Buttons
        footer_layout = QtWidgets.QHBoxLayout()
        self.progress = QtWidgets.QProgressBar(self)
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        footer_layout.addWidget(self.progress)
        footer_layout.addStretch()

        self.calc_btn = QtWidgets.QPushButton("Abrechnung", self)
        self.calc_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #444, stop:1 #222);
                color: #fff;
                border-radius: 8px;
                padding: 8px 28px;
                font-size: 15pt;
                margin-top: 14px;
                border: 1px solid #232323;
            }
            QPushButton:hover {
                background: #ffd600;
                color: #232323;
            }
        """)
        footer_layout.addWidget(self.calc_btn)
        content_layout.addLayout(footer_layout)

        self.calc_btn.clicked.connect(self.perform_abrechnung)

    def format_df_for_view(self, df_numeric):
        """Spalten bereinigen, Index-Spalte befüllen, Beträge formatieren."""
        if df_numeric is None or not isinstance(df_numeric, pd.DataFrame):
            print("[WARN] Kein gültiges DataFrame übergeben.")
            return pd.DataFrame()

        df_view = df_numeric.copy()

        # Spalten ausblenden (inkl. der gewünschten Trinkgeld-Spalte)
        spalten_ignorieren = [
            "kalenderwoche", "zeitstempel", "quelle", "Fahrer/Fahrzeug",
            "trinkgeld_gesamt", "Trinkgeld (Bar)",
        ]
        df_view.drop(columns=[c for c in spalten_ignorieren if c in df_view.columns], inplace=True)

        # Spalten umbenennen
        column_rename = {
            "barumsatz": "Bar",
            "bankomatumsatz": "Karte",
            "trinkgeld_gesamt": "Trinkgeld (Bar)",
            "trinkgeld_nonbar": "Trinkgeld",
            "gesamtumsatz": "Gesamt"
        }
        df_view.rename(columns=column_rename, inplace=True)

        # Index-Spalte befüllen
        indexnamen = []
        for idx, row in df_numeric.iterrows():
            if str(idx) in ["Summe", "Abrechnung"]:
                indexnamen.append(str(idx))
            elif "quelle" in df_numeric.columns and row.get("quelle") in QUELLEN_MAP:
                indexnamen.append(QUELLEN_MAP[row["quelle"]])
            else:
                indexnamen.append(str(idx))
        df_view["Index"] = indexnamen

        # Index-Spalte nach vorne verschieben
        cols = df_view.columns.tolist()
        if "Index" in cols:
            cols.remove("Index")
            df_view = df_view[["Index"] + cols]

        # Währungsformat: alle außer "Index"
        for col in df_view.columns:
            if col == "Index":
                continue
            df_view[col] = pd.to_numeric(df_view[col], errors="coerce")
            df_view[col] = df_view[col].apply(lambda x: f"{x:,.2f} €" if pd.notnull(x) else "")

        return df_view

    def perform_abrechnung(self):
        print("[DEBUG] Abrechnung gestartet")
        self.progress.setVisible(True)
        QtWidgets.QApplication.processEvents()

        # --- Fahrerinfo holen ---
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            normalized = " ".join(self.driver_name.strip().lower().split())
            cursor.execute("""
                SELECT tarif, garage, pauschale, umsatzgrenze FROM fahrer
                WHERE LOWER(TRIM(vorname)) || ' ' || LOWER(TRIM(nachname)) = ?
            """, (normalized,))
            row = cursor.fetchone()
            conn.close()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "DB-Fehler", str(e))
            self.progress.setVisible(False)
            return

        if not row:
            QtWidgets.QMessageBox.warning(
                self,
                "Kein Fahrer gefunden",
                f"'{self.driver_name}' wurde nicht in der Fahrer-Tabelle gefunden."
            )
            self.progress.setVisible(False)
            return

        tarif, garage, pauschale, umsatzgrenze = row

        # Robust gegen NULL/None in der DB
        if garage is None:
            garage = 0.0
        if pauschale is None:
            pauschale = 0.0
        if umsatzgrenze is None:
            umsatzgrenze = 0.0

        # Berechne die aktuelle Kalenderwoche als kw
        kw = self.target_cw  # das ist schon die KW als Zahl

        if tarif == "%":
            def get_sum(col):
                try:
                    val = self.df_numeric.loc["Summe", col]
                    return float(val) if pd.notnull(val) else 0.0
                except Exception:
                    return 0.0

            sum_gesamt = get_sum("gesamtumsatz")
            sum_bankomat = get_sum("bankomatumsatz")
            trinkgeld = get_sum("trinkgeld_nonbar")

            dt = datetime.date.fromisocalendar(self.year, kw, 1)
            monatszahl = dt.month
            montage = sum(1 for d, w in calendar.Calendar().itermonthdays2(self.year, monatszahl) if d and w == 0)
            if not montage:
                QtWidgets.QMessageBox.warning(self, "Fehler", "Für diesen Monat wurden keine Montage erkannt!")
                self.progress.setVisible(False)
                return

            ausgaben = (garage / montage + 0) / 2
            result = ((sum_gesamt + 0 - ausgaben) / 2) + trinkgeld
            print("[DEBUG] Übergabe combo_fz:", self.combo_fz)
            dlg = AbrechnungDialog(
                fahrername=self.driver_name,
                kw=kw,
                pauschale=pauschale,
                bankomatumsatz=sum_bankomat,
                trinkgeld=trinkgeld,
                result=result,
                montage=montage,
                tarif=tarif,
                gesamtumsatz=sum_gesamt,
                garage=garage,
                db_path=self.db_path,
                df_numeric=self.df_numeric,
                year=self.year,
                combo_drv=None,
                combo_fz=self.combo_fz,
                parent=self
            )
            dlg.show()




        elif tarif == "P":
            sum_bankomat = float(self.df_numeric.loc["Summe", "bankomatumsatz"])
            try:
                trinkgeld = float(self.df_numeric.loc["Summe", "trinkgeld_nonbar"])
            except KeyError:
                trinkgeld = 0.0
            dt = datetime.date.fromisocalendar(self.year, kw, 1)
            monatszahl = dt.month
            montage = sum(1 for d, w in calendar.Calendar().itermonthdays2(self.year, monatszahl) if d and w == 0)
            result = sum_bankomat - pauschale + trinkgeld
            print("[DEBUG] Übergabe combo_fz:", self.combo_fz)
            dlg = AbrechnungDialog(
                fahrername=self.driver_name,
                kw=kw,
                pauschale=pauschale,
                bankomatumsatz=sum_bankomat,
                trinkgeld=trinkgeld,
                result=result,
                montage=montage,
                tarif="P",
                gesamtumsatz=None,
                garage=garage,
                db_path=self.db_path,
                df_numeric=self.df_numeric,
                year=self.year,
                combo_drv=None,
                combo_fz=self.combo_fz,  # ✅ hier ebenso!
                parent=self
            )
            dlg.exec()

        self.progress.setVisible(False)

class AbrechnungDialog(CustomDialog):
    def __init__(
        self,
        fahrername, kw, pauschale, bankomatumsatz, trinkgeld, result, montage,
        tarif="P", gesamtumsatz=None, garage=None,
        db_path=None, df_numeric=None, year=None,
        combo_drv=None, combo_fz=None, parent=None
    ):
        super().__init__(parent=parent)

        # Alle wichtigen Werte als Attribute speichern
        self.fahrername = fahrername
        self.kw = kw
        self.pauschale = pauschale
        self.bankomatumsatz = bankomatumsatz
        self.trinkgeld = trinkgeld
        self.result = result
        self.montage = montage
        self.tarif = tarif
        self.gesamtumsatz = gesamtumsatz
        self.garage = garage
        self.db_path = db_path
        self.df_numeric = df_numeric
        self.year = year
        self.combo_drv = combo_drv
        self.combo_fz = combo_fz

        self.setWindowTitle(f"KW{kw} / {fahrername}")
        self.resize(500, 800)

        layout = QtWidgets.QVBoxLayout(self.content)

        fahrer_lbl = QtWidgets.QLabel(f"{fahrername}")
        fahrer_lbl.setAlignment(QtCore.Qt.AlignCenter)
        fahrer_lbl.setStyleSheet("font-size: 22pt; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(fahrer_lbl)

        # Erst das Label erzeugen und zum Layout hinzufügen
        self.result_lbl = QtWidgets.QLabel("0,00 €")
        self.result_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.result_lbl.setStyleSheet(
            "font-size: 38pt; font-weight: bold; color: #ffd600; margin-top: 18px; margin-bottom: 10px;"
        )
        layout.addWidget(self.result_lbl)

        # Jetzt das Ergebnis setzen!
        self.result_lbl.setText(f"{self.result:,.2f} €")

        grid = QtWidgets.QGridLayout()
        grid.setVerticalSpacing(5)
        grid.setHorizontalSpacing(15)
        # Zeilen dynamisch bauen
        zeile = 0
        if self.tarif == "P":
            grid.addWidget(QtWidgets.QLabel("Pauschale:"), zeile, 0, QtCore.Qt.AlignLeft)
            pauschale_lbl = QtWidgets.QLabel(f"{pauschale:,.2f} €")
            pauschale_lbl.setAlignment(QtCore.Qt.AlignRight)
            grid.addWidget(pauschale_lbl, zeile, 1)
            zeile += 1

            grid.addWidget(QtWidgets.QLabel("Bankomatumsatz:"), zeile, 0, QtCore.Qt.AlignLeft)
            bankomat_lbl = QtWidgets.QLabel(f"{bankomatumsatz:,.2f} €")
            bankomat_lbl.setAlignment(QtCore.Qt.AlignRight)
            grid.addWidget(bankomat_lbl, zeile, 1)
            zeile += 1

            grid.addWidget(QtWidgets.QLabel("Trinkgeld:"), zeile, 0, QtCore.Qt.AlignLeft)
            trinkgeld_lbl = QtWidgets.QLabel(f"{trinkgeld:,.2f} €")
            trinkgeld_lbl.setAlignment(QtCore.Qt.AlignRight)
            grid.addWidget(trinkgeld_lbl, zeile, 1)
            zeile += 1
        else:
            grid.addWidget(QtWidgets.QLabel("Gesamtumsatz:"), zeile, 0, QtCore.Qt.AlignLeft)
            gesamt_lbl = QtWidgets.QLabel(f"{gesamtumsatz:,.2f} €")
            gesamt_lbl.setAlignment(QtCore.Qt.AlignRight)
            grid.addWidget(gesamt_lbl, zeile, 1)
            zeile += 1

            grid.addWidget(QtWidgets.QLabel("Bankomatumsatz:"), zeile, 0, QtCore.Qt.AlignLeft)
            bankomat_lbl = QtWidgets.QLabel(f"{bankomatumsatz:,.2f} €")
            bankomat_lbl.setAlignment(QtCore.Qt.AlignRight)
            grid.addWidget(bankomat_lbl, zeile, 1)
            zeile += 1

            # Garage: bereits dividiert durch Montage
            garage_pro_montag = (garage / montage) if montage else 0.0
            grid.addWidget(QtWidgets.QLabel("Garage:"), zeile, 0, QtCore.Qt.AlignLeft)
            garage_lbl = QtWidgets.QLabel(f"{garage_pro_montag:,.2f} €")
            garage_lbl.setAlignment(QtCore.Qt.AlignRight)
            grid.addWidget(garage_lbl, zeile, 1)
            zeile += 1

        self.tank_input = QtWidgets.QLineEdit()
        self.tank_input.setPlaceholderText("Tank")
        self.tank_input.setMaximumWidth(160)
        self.tank_input.setAlignment(QtCore.Qt.AlignRight)
        self.tank_input.setStyleSheet("font-size: 14pt; qproperty-placeholderTextColor: #bbbbbb;")
        grid.addWidget(self.tank_input, zeile, 1)
        zeile += 1

        self.einsteiger_input = QtWidgets.QLineEdit()
        self.einsteiger_input.setPlaceholderText("Einsteiger")
        self.einsteiger_input.setMaximumWidth(160)
        self.einsteiger_input.setAlignment(QtCore.Qt.AlignRight)
        self.einsteiger_input.setStyleSheet("font-size: 14pt; qproperty-placeholderTextColor: #bbbbbb;")
        grid.addWidget(self.einsteiger_input, zeile, 1)
        zeile += 1

        layout.addLayout(grid)

        #self.result_lbl = QtWidgets.QLabel("0,00 €")
        #self.result_lbl.setAlignment(QtCore.Qt.AlignCenter)
        #self.result_lbl.setStyleSheet(
        #    "font-size: 38pt; font-weight: bold; color: #ffd600; margin-top: 18px; margin-bottom: 10px;")
        #layout.addWidget(self.result_lbl)

        ok_btn = QtWidgets.QPushButton("OK")
        ok_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #444, stop:1 #222);
                color: #fff;
                border-radius: 8px;
                padding: 8px 28px;
                font-size: 15pt;
                margin-top: 14px;
                border: 1px solid #232323;
            }
            QPushButton:hover {
                background: #ffd600;
                color: #232323;
            }
        """)
        ok_btn.clicked.connect(self.handle_ok)
        layout.addWidget(ok_btn)

        # Nur bei % dynamisch berechnen!
        if self.tarif == "%":
            self.tank_input.textChanged.connect(self.berechne_ergebnis)
            self.einsteiger_input.textChanged.connect(self.berechne_ergebnis)
            # Initial anzeigen
            self.berechne_ergebnis()

    def berechne_ergebnis(self):
        try:
            tank = float(self.tank_input.text().replace(',', '.')) if self.tank_input.text() else 0.0
        except ValueError:
            tank = 0.0
        try:
            einsteiger = float(self.einsteiger_input.text().replace(',', '.')) if self.einsteiger_input.text() else 0.0
        except ValueError:
            einsteiger = 0.0

        # Monatsgarage auf Wochenbasis umrechnen!
        wochen_garage = self.garage / self.montage if self.montage else 0.0
        # Tank/Einsteiger werden direkt als Wochenwerte erwartet

        fahrer_anteil = (self.gesamtumsatz / 2) - (wochen_garage / 2) - (tank / 2) + (einsteiger / 2) + self.trinkgeld
        unternehmen_anteil = (self.gesamtumsatz / 2) - (wochen_garage / 2) - (tank / 2) + (einsteiger / 2) - self.trinkgeld
        restbetrag = self.bankomatumsatz - unternehmen_anteil

        self.result_lbl.setText(f"{restbetrag:,.2f} €")

    def get_fahrzeug_kennzeichen(self):
        print("[DEBUG] Index:", self.df_numeric.index)
        print("[DEBUG] Spalten:", self.df_numeric.columns)
        print("[DEBUG] Kopf DataFrame:")
        print(self.df_numeric.head())

        # NEU: Suche nach Taxi in Spalte "Index"
        taxi_zeile = self.df_numeric[self.df_numeric["Index"] == "Taxi"]
        if not taxi_zeile.empty:
            fahrzeug_name = taxi_zeile.iloc[0]["Fahrer/Fahrzeug"]
            print("[DEBUG] Taxi-Fahrzeug extrahiert:", fahrzeug_name)
        else:
            # Fallback auf ComboBox
            try:
                if hasattr(self, "combo_fz") and self.combo_fz is not None:
                    fahrzeug_name = self.combo_fz.currentText().strip() if self.combo_fz else None
                    print("[DEBUG] ComboBox-Fahrzeugwert:", fahrzeug_name)
                else:
                    print("[DEBUG] Keine ComboBox für Fahrzeug gefunden.")
                    fahrzeug_name = None
            except Exception:
                print("[DEBUG] ComboBox Fehler.")
                fahrzeug_name = None

        echtes_kennzeichen = None
        if fahrzeug_name:
            try:
                import sqlite3
                from utils import finde_kennzeichen_per_ziffernfolge
                conn = sqlite3.connect(self.db_path)
                echtes_kennzeichen = finde_kennzeichen_per_ziffernfolge(fahrzeug_name, conn)
                conn.close()
                print("[DEBUG] Echtes Kennzeichen gefunden:", echtes_kennzeichen)
            except Exception as e:
                print("[DEBUG] Fahrzeug-Matching-Fehler:", e)
                echtes_kennzeichen = None
        else:
            print("[DEBUG] Kein Fahrzeugname zum Matchen gefunden!")

        return echtes_kennzeichen

    def handle_ok(self):
        # Hole das matched Fahrzeugkennzeichen
        echtes_kennzeichen = self.get_fahrzeug_kennzeichen()

        print("[DEBUG] ECHTES_KENNZEICHEN:", echtes_kennzeichen)
        print("[DEBUG] ComboBox-Wert:", self.combo_fz.currentText() if self.combo_fz else "N/A")
        print("[DEBUG] Übergabe combo_fz:", self.combo_fz)

        # Jetzt WochenberichtDialog aufrufen wie gehabt
        wochenbericht = WochenberichtDialog(
            db_path=self.db_path,
            df_numeric=self.df_numeric,
            fahrername=self.fahrername,
            combo_fz=self.combo_fz,
            fahrzeug=echtes_kennzeichen if echtes_kennzeichen else None, # <-- jetzt immer das ECHTE DB-Kennzeichen
            montage=self.montage,
            kw=self.kw,
            year=self.year,
            tarif=self.tarif,
            pauschale=self.pauschale,
            tank_input=self.tank_input.text(),
            einsteiger_input=self.einsteiger_input.text(),
            garage=self.garage,
        )
        erfolg, msg = wochenbericht.speichern()
        if erfolg:
            QtWidgets.QMessageBox.information(self, "Abrechnung", msg)
        else:
            QtWidgets.QMessageBox.warning(self, "Fehler", msg)
        self.accept()
