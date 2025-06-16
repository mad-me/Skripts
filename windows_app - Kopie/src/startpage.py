from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, QPropertyAnimation, QPoint, QTimer, QEasingCurve
from PySide6.QtGui import QFont, QPixmap

class Startseite(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("startpage")
        self.setMinimumSize(400, 200)
        self.resize(400, 200)
        self.setStyleSheet("""
            QWidget#startpage {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #181a1b, stop:1 #232427);
                border-radius: 36px;
            }
        """)

        self.setWindowOpacity(0.0)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addSpacing(64)

        # Info-Icon
        self.info_btn = QPushButton("ℹ️", self)
        self.info_btn.setFixedSize(44, 44)
        self.info_btn.move(self.width() - 68, 16)
        self.info_btn.setToolTip("Info zu dieser App")
        self.info_btn.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                font-size: 23pt;
                color: #ffd600;
            }
            QPushButton:hover {
                color: #fff;
            }
        """)
        self.info_btn.clicked.connect(
            lambda: QtWidgets.QMessageBox.information(self, "Info", "Willkommen bei El Kaptin KG!\n\nTaxi-Unternehmensabrechnung in Premium-Qualität.")
        )
        self.info_btn.raise_()

        # Logo
        self.logo_label = QLabel()
        pixmap = QPixmap("logo.png")
        if not pixmap.isNull():
            self.logo_label.setPixmap(pixmap.scaledToHeight(108, Qt.SmoothTransformation))
        else:
            self.logo_label.setText("🚕")
            self.logo_label.setStyleSheet("font-size: 74pt; color: #ffd600;")
        self.logo_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.logo_label, alignment=Qt.AlignCenter)
        vbox.addSpacing(24)

        # Haupttitel
        title = QLabel("EL KAPTIN")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 0, QFont.Bold))
        title.setStyleSheet("""
            font-size: 45pt;
            font-weight: 800;
            color: #fafafc;
            letter-spacing: 3px;
            margin-bottom: 8px;
        """)
        vbox.addWidget(title)

        # Slogan-Typewriter
        self.slogan_final = "We move Vienna. Safe. Fast. With Style."
        self.slogan_label = QLabel("")
        self.slogan_label.setAlignment(Qt.AlignCenter)
        self.slogan_label.setFont(QFont("Arial", 0, QFont.Medium))
        self.slogan_label.setStyleSheet("""
            font-size: 18pt;
            color: #bdbdbd;
            letter-spacing: 1.5px;
            margin-bottom: 20px;
        """)
        self.slogan_label.setWordWrap(True)
        vbox.addWidget(self.slogan_label)
        vbox.addSpacing(38)

        # ----------- Apple-Button -----------
        self.btn_start = QPushButton("Jetzt starten")
        self.btn_start.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_start.setFixedHeight(78)
        self.btn_start.setMinimumWidth(260)
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #fffbe6, stop:0.55 #ffe357, stop:1 #ffd600);
                color: #222;
                border-radius: 32px;
                font-size: 24pt;
                font-family: 'SF Pro Display', 'Arial', sans-serif;
                font-weight: 700;
                letter-spacing: 1.3px;
                padding: 18px 48px;
                box-shadow: 0 8px 32px #ffd60048, 0 1.5px 0px #fff6;
                border: none;
                transition: all 0.28s cubic-bezier(.25,.8,.25,1);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #fffcd5, stop:1 #ffe357);
                color: #000;
                filter: brightness(1.06);
                box-shadow: 0 18px 46px #ffd600bb, 0 2.5px 0px #fff9;
                transform: scale(1.035);
            }
            QPushButton:pressed {
                background: #ffd600;
                color: #232323;
                filter: brightness(0.97);
                box-shadow: 0 6px 18px #ffd60088;
                transform: scale(0.99);
            }
        """)
        vbox.addWidget(self.btn_start, alignment=Qt.AlignHCenter)
        vbox.addSpacing(94)

        # Footer
        footer = QLabel("© 2024 El Kaptin KG · Taxi-Unternehmensabrechnung · Vienna")
        footer.setAlignment(Qt.AlignCenter)
        footer.setFont(QFont("Arial", 0, QFont.Normal))
        footer.setStyleSheet("""
            font-size: 12pt;
            color: #464646;
            border-top: 1.5px solid #333;
            padding-top: 12px;
            margin-bottom: 24px;
            letter-spacing: 1px;
            box-shadow: 0 -6px 18px #0005;
        """)
        vbox.addWidget(footer, alignment=Qt.AlignBottom)
        vbox.addSpacing(12)

        QTimer.singleShot(50, self.start_animations)

    def start_animations(self):
        # Fade-in
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(1150)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.fade_anim.start()

        # Logo-Animation (ganz dezent)
        base_pos = self.logo_label.pos()
        new_pos = base_pos - QPoint(0, 8)
        self.logo_label.move(base_pos.x(), base_pos.y() - 8)
        self.logo_anim = QPropertyAnimation(self.logo_label, b"pos", self)
        self.logo_anim.setDuration(1800)
        self.logo_anim.setStartValue(new_pos)
        self.logo_anim.setEndValue(base_pos)
        self.logo_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.logo_anim.start()

        # Info-Icon Position nach Layout
        self.info_btn.move(self.width() - 68, 16)

        # Slogan als Typewriter anzeigen
        self._slogan_step = 0
        self._slogan_timer = QTimer(self)
        self._slogan_timer.timeout.connect(self._type_slogan)
        self._slogan_timer.start(35)

    def _type_slogan(self):
        if self._slogan_step < len(self.slogan_final):
            self.slogan_label.setText(self.slogan_final[:self._slogan_step + 1] + "<span style='color:#ffd600'>|</span>")
            self._slogan_step += 1
        else:
            self.slogan_label.setText(self.slogan_final)
            self._slogan_timer.stop()
