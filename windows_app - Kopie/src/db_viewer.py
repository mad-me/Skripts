from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QStyle
import pandas as pd
import sqlite3
import math
from models import PandasModel
from custom_widgets import CustomDialog, CustomTitleBar

class DbDialog(CustomDialog):
    backClicked = QtCore.Signal()

    def __init__(self, db_path, parent=None):
        super().__init__(parent=parent, title="DB Übersicht")
        self.db_path = db_path

        self.stack = QtWidgets.QStackedWidget()
        main_layout = QtWidgets.QVBoxLayout(self.content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.stack)

        # ---------- Seite 0: Tabellenauswahl ----------
        self.selection_page = QtWidgets.QWidget()
        sel_layout = QtWidgets.QVBoxLayout(self.selection_page)
        sel_layout.setContentsMargins(48, 36, 48, 36)
        sel_layout.setSpacing(24)
        sel_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)

        with sqlite3.connect(self.db_path) as conn:
            self.tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]

        self.table_buttons = []
        self.pro_zeile = 3  # Anzahl Buttons pro Zeile (anpassbar)
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(38)   # Viel Abstand zwischen Buttons

        for idx, table in enumerate(self.tables):
            btn = QtWidgets.QPushButton(table)
            btn.setFixedSize(200, 58)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 14pt; 
                    padding: 7px 14px;
                    border-radius: 12px; 
                    background: #292929; 
                    color: #ffd600;
                }
                QPushButton:hover {
                    font-size: 17pt;
                    font-weight: bold; 
                    background: #ffd600; 
                    color: #232323;
                    padding: 2px 5px;
                }
            """)
            btn.clicked.connect(lambda _, t=table: self.load_table_page(t))
            grid.addWidget(btn, idx // self.pro_zeile, idx % self.pro_zeile)
            self.table_buttons.append(btn)

        sel_layout.addStretch(1)
        sel_layout.addLayout(grid)
        sel_layout.addStretch(10)

        self.stack.addWidget(self.selection_page)

        # --- Dynamische Größe für Auswahlseite ---
        self._resize_to_button_grid()

        # ---------- Seite 1: Tabellenansicht ----------
        self.table_page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.table_page)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        self.combo_tables = QtWidgets.QComboBox()
        self.combo_tables.setVisible(False)
        layout.addWidget(self.combo_tables)

        self.filter_layout = QtWidgets.QHBoxLayout()
        self.filter_layout.setSpacing(10)
        layout.addLayout(self.filter_layout)

        self.table = QtWidgets.QTableView()
        self.table.setMinimumWidth(700)
        self.table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.table.setStyleSheet("""
            QTableView {
                background-color: #232323;
                color: #e0e0e0;
                border: none;
                font-size: 14pt;
            }
            QHeaderView::section {
                background-color: transparent;
                border: none;
                font-size: 18pt;
            }
            QTableView::item {
                padding-top: 8px;
                padding-bottom: 8px;
                padding-left: 12px;
                padding-right: 12px;
            }
        """)
        layout.addWidget(self.table, 1)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(18)
        button_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #444, stop:1 #222);
                color: #fff;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 14pt;
                border: 1.5px solid #232323;
            }
            QPushButton:hover {
                background: #ffd600;
                color: #232323;
            }
        """

        self.btn_add = QtWidgets.QPushButton("Zeile hinzufügen")
        self.btn_add.setStyleSheet(button_style)
        self.btn_delete = QtWidgets.QPushButton("Zeile löschen")
        self.btn_delete.setStyleSheet(button_style)
        self.btn_save = QtWidgets.QPushButton("Speichern")
        self.btn_save.setStyleSheet(button_style)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addStretch(1)
        layout.addLayout(btn_layout)

        self.stack.addWidget(self.table_page)
        self.stack.setCurrentIndex(0)

        self.model = None
        self.df = None
        self.table_name = None
        self.active_filters = {}

        self.btn_add.clicked.connect(self.add_row)
        self.btn_delete.clicked.connect(self.delete_row)
        self.btn_save.clicked.connect(self.save_changes)
        self.load_table_list()

    def _resize_to_button_grid(self):
        # Dynamisch Höhe und Breite je nach Zahl der Buttons/Tabellen
        anzahl = len(self.tables)
        pro_zeile = self.pro_zeile
        anz_zeilen = math.ceil(anzahl / pro_zeile)
        hoehe_button = 58
        abstand_buttons = 38
        margins = 170
        gesamt_hoehe = (anz_zeilen * hoehe_button) + ((anz_zeilen - 1) * abstand_buttons) + margins
        gesamt_hoehe = max(gesamt_hoehe, 340)

        breite_buttons = 200
        abstand_spalten = 38
        gesamt_breite = (pro_zeile * breite_buttons) + ((pro_zeile - 1) * abstand_spalten) + 120
        gesamt_breite = max(gesamt_breite, 480)

        self.resize(gesamt_breite, gesamt_hoehe)
        self.setMinimumSize(gesamt_breite - 60, gesamt_hoehe - 60)

    def load_table_list(self):
        with sqlite3.connect(self.db_path) as conn:
            tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        self.combo_tables.clear()
        self.combo_tables.addItems(tables)

    def load_table_data(self, idx=None, filtered=False):
        self.stack.setCurrentIndex(1)
        self.titlebar.back_btn.setVisible(True)
        self.titlebar.setTitle(f"Datenbank: {self.combo_tables.currentText()}")
        self.table_name = self.combo_tables.currentText()
        self.titlebar.backClicked.connect(self._on_back_clicked)
        if not self.table_name:
            QtWidgets.QMessageBox.warning(self, "Fehler", "Keine Tabelle ausgewählt.")
            return

        query = f"SELECT * FROM [{self.table_name}]"
        params = []
        filter_clauses = []

        if filtered and self.active_filters:
            for key, widget in self.active_filters.items():
                if isinstance(widget, QtWidgets.QComboBox):
                    if widget.currentIndex() > 0:
                        val = widget.currentText().strip()
                        filter_clauses.append(f"{key} = ?")
                        params.append(val)
                elif isinstance(widget, QtWidgets.QListWidget):
                    selected = [item.text().replace("KW", "") for item in widget.selectedItems()]
                    if selected:
                        filter_clauses.append(f"{key} IN ({','.join(['?'] * len(selected))})")
                        params.extend(selected)
        if filter_clauses:
            query += " WHERE " + " AND ".join(filter_clauses)

        with sqlite3.connect(self.db_path) as conn:
            self.df = pd.read_sql_query(query, conn, params=params)

        if "Index" in self.df.columns:
            self.df.drop(columns=["Index"], inplace=True)

        float_cols = self.df.select_dtypes(include=['float']).columns
        if len(float_cols) > 0:
            self.df[float_cols] = self.df[float_cols].round(2)

        self.model = PandasModel(self.df)
        self.table.setModel(self.model)
        self.table.verticalHeader().setVisible(False)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        header = self.table.horizontalHeader()
        col_count = self.table.model().columnCount()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.setMinimumSectionSize(40)

        metrics = self.table.fontMetrics()
        for col in range(col_count):
            header_text = self.table.model().headerData(col, QtCore.Qt.Horizontal)
            header_width = metrics.horizontalAdvance(str(header_text)) + 32
            col_width = max(self.table.columnWidth(col), header_width)
            self.table.setColumnWidth(col, col_width)

        # ------ Fenstergröße optimal anpassen (dynamisch!) ------
        # Breite berechnen
        total_width = self.table.verticalHeader().width()
        for col in range(self.table.model().columnCount()):
            total_width += self.table.columnWidth(col)
        # Scrollbar, falls nötig
        if self.table.verticalScrollBar().isVisible():
            total_width += self.table.verticalScrollBar().width()
        total_width += 36  # etwas Puffer/Rand

        # Höhe berechnen (maximal 25 Zeilen zur Berechnung heranziehen)
        total_height = self.table.horizontalHeader().height()
        row_count = self.table.model().rowCount()
        for row in range(min(row_count, 25)):
            total_height += self.table.rowHeight(row)
        # Scrollbar, falls nötig
        if self.table.horizontalScrollBar().isVisible():
            total_height += self.table.horizontalScrollBar().height()
        # Buttons, Filter und etwas Puffer
        total_height += 180

        # Maximalgröße (optional, falls du das Fenster nicht größer als Bildschirm willst)
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        total_width = min(total_width, screen.width() - 100)
        total_height = min(total_height, screen.height() - 100)

        self.resize(total_width, total_height)
        self.setMinimumSize(650, 420)

        # Fenster zentralisieren (relativ zum aktuellen Bildschirm)
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.primaryScreen()
        centerPoint = screen.availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def update_filters(self, table_name):
        while self.filter_layout.count():
            item = self.filter_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.active_filters = {}

        if not table_name:
            return

        def add_combo(label, sql, key=None):
            cb = QtWidgets.QComboBox()
            cb.setMinimumWidth(60)
            cb.setMinimumWidth(70)
            cb.addItem(label)
            with sqlite3.connect(self.db_path) as conn:
                werte = sorted(set(str(r[0]) for r in conn.execute(sql) if r[0]))
            cb.addItems(werte)
            cb.setCurrentIndex(0)
            cb.setStyleSheet("min-height: 28px; font-size: 12pt;")
            self.filter_layout.addWidget(cb)
            self.active_filters[key or label] = cb
            cb.currentIndexChanged.connect(lambda _: self.apply_filter())

        def add_list(label, sql, key=None):
            lw = QtWidgets.QListWidget()
            lw.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
            with sqlite3.connect(self.db_path) as conn:
                items = sorted(set(str(r[0]) for r in conn.execute(sql) if r[0]))
            for item in items:
                lw.addItem(f"KW{item}" if label.startswith("Kalenderwoche") else item)
            lw.setMinimumWidth(120)
            lw.setStyleSheet("min-height: 60px; font-size: 12pt;")
            self.filter_layout.addWidget(lw)
            self.active_filters[key or label] = lw
            lw.itemSelectionChanged.connect(self.apply_filter)

        if table_name == "fahrzeuge":
            add_combo("Kennzeichen wählen…", "SELECT DISTINCT kennzeichen FROM fahrzeuge", "kennzeichen")
        elif table_name == "fahrer":
            add_combo("Dienstnehmernummer wählen…", "SELECT DISTINCT dienstnehmernummer FROM fahrer", "dienstnehmernummer")
            add_combo("Vorname wählen…", "SELECT DISTINCT vorname FROM fahrer", "vorname")
            add_combo("Nachname wählen…", "SELECT DISTINCT nachname FROM fahrer", "nachname")
            status_cb = QtWidgets.QComboBox()
            status_cb.addItems(["Status wählen…", "0", "1"])
            status_cb.setCurrentIndex(0)
            status_cb.setStyleSheet("min-height: 28px; font-size: 12pt;")
            self.filter_layout.addWidget(status_cb)
            self.active_filters["status"] = status_cb
            status_cb.currentIndexChanged.connect(lambda _: self.apply_filter())
        elif table_name == "umsatz_40100":
            add_combo("Fahrzeug wählen…", "SELECT DISTINCT fahrzeug FROM umsatz_40100", "fahrzeug")
            add_list("Kalenderwoche wählen…", "SELECT DISTINCT kalenderwoche FROM umsatz_40100", "kalenderwoche")
        elif table_name in ("umsatz_bolt", "umsatz_uber"):
            add_combo("Fahrer wählen…", f"SELECT DISTINCT Driver FROM {table_name}", "Driver")
            add_list("Kalenderwoche wählen…", f"SELECT DISTINCT kalenderwoche FROM {table_name}", "kalenderwoche")
        elif table_name == "internal":
            add_combo("Woche wählen…", "SELECT DISTINCT week FROM internal", "week")
            add_combo("Fahrzeug wählen…", "SELECT DISTINCT vehicle FROM internal", "vehicle")
        elif table_name == "zuordnung_40100":
            add_combo("Kennung wählen…", "SELECT DISTINCT kennung FROM zuordnung_40100", "kennung")
            add_combo("Verkehrskennzeichen wählen…", "SELECT DISTINCT verkehrskennzeichen FROM zuordnung_40100", "verkehrskennzeichen")
        elif table_name == "gehalt":
            add_combo("Dienstnehmernummer wählen…", "SELECT DISTINCT dienstnehmernummer FROM gehalt", "dienstnehmernummer")
            add_combo("Dienstnehmer wählen…", "SELECT DISTINCT dienstnehmer FROM gehalt", "dienstnehmer")
            add_combo("Monat/Jahr wählen…", "SELECT DISTINCT monat_jahr FROM gehalt", "monat_jahr")
        elif table_name == "funk_40100":
            add_combo("Verkehrskennzeichen wählen…", "SELECT DISTINCT verkehrskennzeichen FROM funk_40100", "verkehrskennzeichen")
            add_combo("Monat/Jahr wählen…", "SELECT DISTINCT monat_jahr FROM funk_40100", "monat_jahr")

    def _on_back_clicked(self):
        self.stack.setCurrentIndex(0)
        self._resize_to_button_grid()
        self.titlebar.back_btn.setVisible(False)
        self.titlebar.setTitle("Tabellenauswahl")

    def apply_filter(self):
        self.load_table_data(filtered=True)

    def load_table_page(self, table_name):
        if table_name in self.tables:
            self.combo_tables.clear()
            self.combo_tables.addItems(self.tables)
            self.combo_tables.setCurrentText(table_name)
            self.table_name = table_name
            self.update_filters(table_name)
            self.load_table_data()
            self.stack.setCurrentIndex(1)

    def add_row(self):
        if self.df is not None:
            self.df.loc[len(self.df)] = ["" for _ in self.df.columns]
            self.model = PandasModel(self.df)
            self.table.setModel(self.model)
            self.table.verticalHeader().setVisible(False)

    def delete_row(self):
        idx = self.table.currentIndex()
        if self.df is not None and idx.isValid():
            self.df = self.df.drop(idx.row()).reset_index(drop=True)
            self.model = PandasModel(self.df)
            self.table.setModel(self.model)
            self.table.verticalHeader().setVisible(False)

    def save_changes(self):
        if self.df is not None and self.table_name:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(f"DELETE FROM [{self.table_name}]")
                self.df.drop(columns=["Index"], inplace=True, errors="ignore")
                self.df.to_sql(self.table_name, conn, if_exists="append", index=False)
            QtWidgets.QMessageBox.information(self, "Speichern", "Änderungen gespeichert!")
