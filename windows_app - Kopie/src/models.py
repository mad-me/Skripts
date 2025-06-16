import os
import datetime
import pandas as pd
from PySide6.QtCore import QAbstractTableModel, Qt, QThread, Signal
from PySide6.QtGui import QFont


class PandasModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame):
        super().__init__()
        df = df.copy()
        if "Index" in df.columns:
            cols = ["Index"] + [c for c in df.columns if c != "Index"]
            df = df[cols]
            self._index_labels = list(df["Index"])
        else:
            self._index_labels = list(df.index)
        self._df = df.reset_index(drop=True)

    def rowCount(self, parent=None):
        return self._df.shape[0]

    def columnCount(self, parent=None):
        return self._df.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        wert = self._df.iat[row, col]

        # Zellinhalt zurückgeben
        if role == Qt.DisplayRole:
            return str(wert)

        # Zeilen 'Summe' und 'Abrechnung' fett machen (über Indexspalte)
        if role == Qt.FontRole:
            idx_label = str(self._df.iat[row, 0])  # Spalte "Index"
            if idx_label in ["Summe", "Abrechnung"]:
                font = QFont()
                font.setBold(True)
                return font
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            colname = self._df.columns[section]
            return "" if colname == "Index" else colname
        return section + 1


class DataLoader(QThread):
    """
    Lädt eine CSV-Datei (data/meine_daten.csv) in einem Thread asynchron.
    Bei erfolgreichem Laden wird das DataFrame über data_ready-Signal ausgesendet.
    """
    data_ready = Signal(pd.DataFrame)

    def run(self):
        encodings = ["utf-8", "cp1252"]
        df = None
        for enc in encodings:
            try:
                df = pd.read_csv("data/meine_daten.csv", sep=";", encoding=enc)
                print(f"CSV erfolgreich geladen mit Encoding: {enc}")
                break
            except UnicodeDecodeError:
                print(f"Fehler mit Encoding {enc}, versuche nächstes…")
            except Exception as e:
                print(f"Anderer Fehler beim Laden der CSV ({enc}): {e}")
                df = pd.DataFrame()
                break

        if df is None:
            print("Konnte CSV mit keinem getesteten Encoding lesen, gebe leeres DataFrame zurück.")
            df = pd.DataFrame()

        self.data_ready.emit(df)

    class FilteredDataLoader(QThread):
        """
        Lädt dieselbe CSV-Datei und filtert nach Fahrzeug und Fahrer.
        Gibt das gefilterte DataFrame über data_ready-Signal zurück.
        """
        data_ready = Signal(pd.DataFrame)

        def __init__(self, fahrzeug: str, fahrer: str, parent=None):
            super().__init__(parent=parent)
            self.fahrzeug = fahrzeug
            self.fahrer  = fahrer

        def run(self):
            try:
                df = pd.read_csv("data/meine_daten.csv", sep=";", encoding="cp1252")
            except Exception as e:
                print(f"Fehler beim Lesen der CSV: {e}")
                df = pd.DataFrame()
                self.data_ready.emit(df)
                return

            # Filter anwenden
            df_filt = df[
                (df["Fahrzeug"] == self.fahrzeug) &
                (df["Fahrer"]  == self.fahrer)
            ]
            self.data_ready.emit(df_filt)