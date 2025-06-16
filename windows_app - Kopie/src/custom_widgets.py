from utils import center_window
from PySide6 import QtWidgets, QtCore

class CustomTitleBar(QtWidgets.QWidget):
    backClicked = QtCore.Signal()

    def __init__(self, parent=None, title_text="", show_back=False):
        super().__init__(parent)
        self.setFixedHeight(48)  # Passt zur Button-Größe

        # Titel-Label
        self.title_label = QtWidgets.QLabel(title_text, self)
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setStyleSheet(
            "color: #e0e0e0; font-size: 13pt; font-weight: bold; letter-spacing: 1px; padding: 0; margin: 0;"
        )
        self.title_label.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        # Layout für die Buttons
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)
        layout.setAlignment(QtCore.Qt.AlignVCenter)

        button_diameter = 24
        button_radius = 12

        button_style = f"""
            QPushButton {{
                background: transparent;
                color: #ffd600;
                font-size: 13pt;
                border: 1.2px solid #555555;
                border-radius: {button_radius}px;
                min-width: {button_diameter}px; min-height: {button_diameter}px;
                max-width: {button_diameter}px; max-height: {button_diameter}px;
                padding: 0;
            }}
            QPushButton:hover {{
                color: #232323;
                background: #ffd600;
                border-color: #ffd600;
            }}
        """

        close_style = f"""
            QPushButton {{
                background: transparent;
                color: #ff3333;
                font-size: 15pt;
                border: 1.2px solid #555555;
                border-radius: {button_radius}px;
                min-width: {button_diameter}px; min-height: {button_diameter}px;
                max-width: {button_diameter}px; max-height: {button_diameter}px;
                padding: 0;
            }}
            QPushButton:hover {{
                color: #fff;
                background: #c80000;
                border-color: #ff3333;
            }}
        """

        # Back-Button (optional ganz links)
        self.back_btn = QtWidgets.QPushButton("←")
        self.back_btn.setFixedSize(button_diameter, button_diameter)
        self.back_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.back_btn.setStyleSheet(button_style)
        self.back_btn.clicked.connect(self.backClicked.emit)
        self.back_btn.setVisible(show_back)
        layout.addWidget(self.back_btn)

        # Stretch, dann Buttons rechts
        layout.addStretch(1)

        # Minimize
        self.min_btn = QtWidgets.QPushButton("-")
        self.min_btn.setFixedSize(button_diameter, button_diameter)
        self.min_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.min_btn.setStyleSheet(button_style)
        self.min_btn.clicked.connect(lambda: self.window().showMinimized())
        layout.addWidget(self.min_btn)

        # Maximize/Restore
        self.max_btn = QtWidgets.QPushButton("□")
        self.max_btn.setFixedSize(button_diameter, button_diameter)
        self.max_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.max_btn.setStyleSheet(button_style)
        self.max_btn.clicked.connect(self.toggle_max_restore)
        layout.addWidget(self.max_btn)

        # Close
        self.close_btn = QtWidgets.QPushButton("×")
        self.close_btn.setFixedSize(button_diameter, button_diameter)
        self.close_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.close_btn.setStyleSheet(close_style)
        self.close_btn.clicked.connect(lambda: self.window().close())
        layout.addWidget(self.close_btn)

        self._drag_pos = None

    def resizeEvent(self, event):
        # Das Titel-Label immer auf volle Fläche ziehen
        self.title_label.setGeometry(0, 0, self.width(), self.height())
        return super().resizeEvent(event)

    def setTitle(self, text):
        self.title_label.setText(text)

    def toggle_max_restore(self):
        win = self.window()
        if win.isMaximized():
            win.showNormal()
        else:
            win.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == QtCore.Qt.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class CustomDialog(QtWidgets.QDialog):
    def __init__(self, title="Dialog", parent=None):
        super().__init__(parent=parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

        # <---- HIER: Ein Hintergrundwidget für Border, Background, Radius
        self.bg_widget = QtWidgets.QWidget(self)
        self.bg_widget.setObjectName("DialogBackground")
        self.bg_widget.setStyleSheet("""
            QWidget#DialogBackground {
                background-color: #232323;
                border-radius: 22px;
                border: 2.3px solid #555;
            }
        """)
        self.bg_widget.setGeometry(self.rect())
        self.bg_widget.lower()  # Hintergrund nach unten

        # Layout auf das Hintergrundwidget setzen
        main_vbox = QtWidgets.QVBoxLayout(self.bg_widget)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)

        self.titlebar = CustomTitleBar(self, title_text=title)
        main_vbox.addWidget(self.titlebar)

        self.content = QtWidgets.QWidget()
        self.content.setStyleSheet("background: transparent;")
        main_vbox.addWidget(self.content, 1)

        # Damit sich das bg_widget immer anpasst:
        self.resizeEvent = self._resize_bg

        QtCore.QTimer.singleShot(0, lambda: center_window(self))

    def _resize_bg(self, event):
        self.bg_widget.setGeometry(self.rect())
        return super().resizeEvent(event)
