import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "SQL", "EKK.db"))
UI_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "ui", "mainwindow.ui"))