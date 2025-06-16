from PySide6 import QtWidgets, QtCore

def erstelle_indexseite(parent=None):
    index_widget = QtWidgets.QWidget(parent)
    index_widget.setObjectName("indexpage")  # Wichtig, damit das Stylesheet greift!

    vbox = QtWidgets.QVBoxLayout(index_widget)
    vbox.setAlignment(QtCore.Qt.AlignCenter)
    vbox.setContentsMargins(40, 60, 40, 60)
    vbox.setSpacing(48)

    # Überschrift
    label = QtWidgets.QLabel("Was möchtest du tun?")
    label.setAlignment(QtCore.Qt.AlignCenter)
    label.setStyleSheet("font-size: 28pt; font-weight: 700; color: #ffd600; margin-bottom: 16px;")
    vbox.addWidget(label)

    # Buttons, KEIN eigenes Styling nötig!
    btn_weekly = QtWidgets.QPushButton("Abrechnung")
    btn_weekly.setObjectName("weeklyButton")

    btn_db = QtWidgets.QPushButton("Daten verwalten")
    btn_db.setObjectName("btnDbUebersicht")

    btn_monthly = QtWidgets.QPushButton("Monatsbericht")  # <---- HINZUGEFÜGT
    btn_monthly.setObjectName("monthlyButton")

    # Buttons hinzufügen
    vbox.addWidget(btn_weekly, alignment=QtCore.Qt.AlignHCenter)
    vbox.addWidget(btn_monthly, alignment=QtCore.Qt.AlignHCenter)
    vbox.addWidget(btn_db, alignment=QtCore.Qt.AlignHCenter)
    vbox.addStretch(2)

    return index_widget, btn_weekly, btn_monthly, btn_db