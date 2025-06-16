from PySide6 import QtWidgets, QtCore

class AbrechnungsSeite(QtWidgets.QWidget):
    def __init__(self, fahrer_liste, fahrzeug_liste, aktuelle_kw, parent=None):
        super().__init__(parent)
        self.setObjectName("abrechnungspage")
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.setContentsMargins(50, 40, 50, 40)
        vbox.setSpacing(28)

        label = QtWidgets.QLabel("Wöchentliche Abrechnung")
        label.setStyleSheet("font-size: 28pt; font-weight: 800; color: #ffd600; margin-bottom:18px;")
        label.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(label)

        self.combo_drv = QtWidgets.QComboBox()
        self.combo_drv.addItems(fahrer_liste)
        self.combo_drv.setPlaceholderText("Fahrer wählen...")
        vbox.addWidget(self.combo_drv)

        self.combo_fz = QtWidgets.QComboBox()
        self.combo_fz.addItems(fahrzeug_liste)
        self.combo_fz.setPlaceholderText("Fahrzeug wählen...")
        vbox.addWidget(self.combo_fz)

        self.combo_kw = QtWidgets.QComboBox()
        self.combo_kw.addItems(["Letzte Woche", "Vorletzte Woche"])
        for kw in range(aktuelle_kw - 3, 0, -1):
            self.combo_kw.addItem(f"KW {kw}")
        self.combo_kw.setPlaceholderText("Kalenderwoche wählen...")
        vbox.addWidget(self.combo_kw)

        self.load_btn = QtWidgets.QPushButton("Abrechnen")
        self.load_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffe066, stop:1 #ffd600);
                color: #222;
                border-radius: 18px;
                padding: 16px 34px;
                font-size: 19pt;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #ffd600;
                color: #111;
            }
        """)
        vbox.addWidget(self.load_btn, alignment=QtCore.Qt.AlignHCenter)

