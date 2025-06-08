import os
import sys
from PySide6 import QtUiTools, QtCore, QtWidgets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_PATH = os.path.normpath(os.path.join(BASE_DIR, os.pardir, "ui", "mainwindow.ui"))

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
