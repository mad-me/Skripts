# models.py
import pandas as pd
from PySide6.QtCore import QAbstractTableModel, Qt, QThread, Signal
from PySide6.QtGui import QFont

class PandasModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df.copy().reset_index(drop=True)

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
        if role == Qt.DisplayRole:
            return str(wert)
        if role == Qt.FontRole:
            idx_label = str(self._df.iat[row, 0])  # Erste Spalte meist Index/Summe
            if idx_label.lower() in ["summe", "abrechnung"]:
                font = QFont()
                font.setBold(True)
                return font
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            colname = self._df.columns[section]
            return "" if colname.lower() == "index" else colname
        return section + 1

# Hilfsfunktion für Indexnamen
def setze_indexnamen(df):
    df = df.copy()
    indexnamen = []
    for idx, row in df.iterrows():
        if str(idx).lower() in ["summe", "abrechnung"]:
            indexnamen.append(str(idx))
        elif "quelle" in df.columns and row["quelle"] in {"umsatz_bolt":"Bolt","umsatz_uber":"Uber","umsatz_40100":"Taxi"}.keys():
            indexnamen.append({"umsatz_bolt":"Bolt","umsatz_uber":"Uber","umsatz_40100":"Taxi"}[row["quelle"]])
        else:
            indexnamen.append(str(idx))
    df["Index"] = indexnamen
    return df
