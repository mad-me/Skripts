import os
import datetime
import calendar
import sqlite3
import pandas as pd
from PySide6 import QtWidgets, QtCore
from db_access import lade_fahrzeuge
from custom_widgets import CustomDialog

MONATSNAMEN = [
    "Jänner", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]

class MonatsberichtSeite(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("monatsberichtseite")

        self.vbox = QtWidgets.QVBoxLayout(self)
        self.vbox.setAlignment(QtCore.Qt.AlignTop)
        self.vbox.setContentsMargins(40, 40, 40, 40)
        self.vbox.setSpacing(28)

        label = QtWidgets.QLabel("Monatsbericht")
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet("font-size: 24pt; font-weight: 700; color: #ffd600;")
        self.vbox.addWidget(label)

        self.combo_monat = QtWidgets.QComboBox()
        self.combo_monat.addItems(MONATSNAMEN)
        self.combo_monat.setCurrentIndex(datetime.date.today().month - 1)
        self.combo_monat.setMinimumWidth(250)
        self.vbox.addWidget(self.combo_monat, alignment=QtCore.Qt.AlignHCenter)

        self.combo_fz = QtWidgets.QComboBox()
        self.combo_fz.setMinimumWidth(250)
        self.combo_fz.setPlaceholderText("Fahrzeug auswählen")
        self.vbox.addWidget(self.combo_fz, alignment=QtCore.Qt.AlignHCenter)

        self.btn_bericht = QtWidgets.QPushButton("Bericht erstellen")
        self.btn_bericht.setMinimumWidth(250)
        self.btn_bericht.setStyleSheet("font-size: 16pt; font-weight: 700;")
        self.vbox.addWidget(self.btn_bericht, alignment=QtCore.Qt.AlignHCenter)

        self.lade_fahrzeuge()
        self.btn_bericht.clicked.connect(self.erstelle_bericht)

    def lade_fahrzeuge(self):
        try:
            fahrzeuge = lade_fahrzeuge()
            self.combo_fz.clear()
            self.combo_fz.addItem("")
            self.combo_fz.addItems(fahrzeuge)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Fehler", f"Fahrzeuge konnten nicht geladen werden:\n{e}")

    def erstelle_bericht(self):
        monat = self.combo_monat.currentIndex() + 1
        jahr = datetime.date.today().year
        fahrzeug = self.combo_fz.currentText().strip()

        if not fahrzeug:
            QtWidgets.QMessageBox.warning(self, "Fehler", "Bitte wähle ein Fahrzeug.")
            return

        kw_liste = self.get_calendar_weeks_for_month(jahr, monat)
        if not kw_liste:
            QtWidgets.QMessageBox.information(self, "Hinweis", "Keine Kalenderwochen für diesen Monat gefunden.")
            return

        # Datenbankzugriff
        base_dir = os.path.dirname(__file__)
        db_path = os.path.normpath(os.path.join(base_dir, "..", "..", "SQL", "EKK.db"))

        try:
            conn = sqlite3.connect(db_path)
            # Abfrage wie bisher, aber nur für gefilterte Wochen
            df = pd.read_sql_query(
                f"SELECT * FROM internal WHERE week IN ({','.join(['?'] * len(kw_liste))}) AND vehicle = ?",
                conn,
                params=kw_liste + [fahrzeug]
            )
            conn.close()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Fehler", str(e))
            return

        if df.empty:
            QtWidgets.QMessageBox.information(self, "Keine Daten", "Für Auswahl wurden keine Einträge gefunden.")
            return

        rename_map = {
            "driver": "Driver",
            "vehicle": "Vehicle",
            "turnover": "Turnover",
            "income": "Income",
            "running_cost": "Fuel",
            "garage": "Garage",
            "loan": "Loan",
            "insurance": "C.I.",
            "accounting": "Acco",
            "disponent": "Dispo",
            "health_insurance": "H.C.",
            "sales_volume_tax": "S.V.T.",
            "input_tax": "Ref",
            "einsteiger": "+",
            "untaxed_income": "ut.P.",
            "week": "cw"
        }

        df = df.rename(columns=rename_map)
        df = df.reset_index(drop=True)
        dialog = MonatsberichtDialog(df, parent=self)
        dialog.exec()

    def get_calendar_weeks_for_month(self, year, month):
        """
        Liefert alle ISO-KWs, deren SONNTAG im angegebenen Monat liegt.
        """
        k = calendar.Calendar(firstweekday=0)
        wochen = set()
        for week in k.monthdatescalendar(year, month):
            so = week[6]  # Sonntag der Woche
            if so.month == month:
                wochen.add(so.isocalendar()[1])
        return sorted(list(wochen))

class MonatsberichtDialog(CustomDialog):
    def __init__(self, df, parent=None):
        super().__init__(title="", parent=parent)

        # --- Dynamische Breite je nach Spaltenanzahl ---
        basis = 180
        min_width = 900
        max_width = 1400
        breite = max(min_width, min(max_width, int(len(df.columns) * basis)))
        self.resize(breite, 400)

        layout = QtWidgets.QVBoxLayout(self.content)
        layout.setSpacing(18)
        layout.setContentsMargins(28, 18, 28, 18)

        # --- Tabelle ---
        table = QtWidgets.QTableView(self)
        table.setModel(PandasModel(df))
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        table.setEditTriggers(QtWidgets.QTableView.NoEditTriggers)
        table.setSortingEnabled(True)
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(False)
        table.verticalHeader().hide()
        table.setShowGrid(False)
        table.setStyleSheet("""
            QTableView {
                background: transparent;
                alternate-background-color: rgba(255,255,255,0.02);
                font-size: 15pt;
                border-radius: 12px;
                gridline-color: transparent;
            }
            QHeaderView::section {
                background: transparent;
                color: #ffd600;
                font-size: 15pt;
                font-weight: bold;
                border: none;
                border-radius: 0;
                padding: 10px 6px;
            }
            QTableView::item:selected {
                background: #ffd600;
                color: #232323;
            }
        """)
        layout.addWidget(table)

        # --- Summenwerte (direkt unter der Tabelle, als eine Zeile) ---
        summen_felder = [
            ("Gesamtumsatz", "gesamtumsatz"),
            ("Einkommen gesamt", "income"),
            ("Gesamte Kosten", "running_cost"),
        ]
        # --- Summenwerte (direkt unter der Tabelle, als eine Zeile) ---
        sum_layout = QtWidgets.QHBoxLayout()
        sum_layout.addStretch(1)

        # Helper zum holt Wert (0.0 falls nicht da)
        def col_sum(col):
            return float(df[col].sum()) if col in df.columns else 0.0

        # 1. Total turnover
        total_turnover = col_sum("Turnover") + col_sum("+")
        sum_layout.addWidget(QtWidgets.QLabel("TT:"))
        sum_layout.addWidget(QtWidgets.QLabel(f"{total_turnover:,.2f} €"))

        # 2. Total cost
        total_cost = (
                col_sum("Fuel  ") +
                col_sum("Garage") +
                col_sum("Loan") +
                col_sum("ACC") +
                col_sum("Dispo") +
                col_sum("H.C.") +
                col_sum("S.V.T.")
        )
        sum_layout.addWidget(QtWidgets.QLabel("Total Cost:"))
        sum_layout.addWidget(QtWidgets.QLabel(f"{total_cost:,.2f} €"))

        # 3. Income
        income = col_sum("Income")
        sum_layout.addWidget(QtWidgets.QLabel("Income:"))
        sum_layout.addWidget(QtWidgets.QLabel(f"{income:,.2f} €"))

        # 4. Profit untaxed
        profit_untaxed = col_sum("ut.P.")
        sum_layout.addWidget(QtWidgets.QLabel("ut.P.:"))
        sum_layout.addWidget(QtWidgets.QLabel(f"{profit_untaxed:,.2f} €"))

        # Anzahl Einträge immer anzeigen
        sum_layout.addWidget(QtWidgets.QLabel("Anzahl Einträge:"))
        sum_layout.addWidget(QtWidgets.QLabel(str(len(df))))
        sum_layout.addStretch(1)
        layout.addLayout(sum_layout)

class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df = df

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.columns)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        value = self._df.iloc[index.row(), index.column()]
        if role == QtCore.Qt.DisplayRole:
            if isinstance(value, float):
                return f"{value:,.2f}"
            return str(value)
        elif role == QtCore.Qt.TextAlignmentRole:
            if isinstance(value, (float, int)):
                return QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            return QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        return None

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return str(self._df.columns[section])
            elif orientation == QtCore.Qt.Vertical:
                return str(self._df.index[section])
        return None
