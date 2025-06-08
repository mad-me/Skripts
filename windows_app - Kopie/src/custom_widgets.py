from PySide6 import QtWidgets, QtCore

class CustomTitleBar(QtWidgets.QWidget):
    def __init__(self, parent=None, title_text=""):
        super().__init__(parent)
        self.setFixedHeight(38)
        self.setStyleSheet("""
            background-color: #232323;
            border-top-left-radius: 18px;  
            border-top-right-radius: 18px;
        """)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        # Title
        self.title_label = QtWidgets.QLabel(title_text)
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #e0e0e0; font-size: 16pt; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(self.title_label, 1)

        # Gemeinsames Button-StyleSheet mit Border!
        button_style = """
            QPushButton {
                background: none;
                color: #ffd600;
                font-size: 16pt;
                border: 1.3px solid #555555;    /* <- zarte Border */
                border-radius: 7px;
                padding-left: 0; padding-right: 0;
            }
            QPushButton:hover {
                color: #232323;
                background: #ffd600;
                border-color: #ffd600;           /* Bei Hover auch Border in gelb */
            }
        """

        # Minimize
        self.min_btn = QtWidgets.QPushButton("-")
        self.min_btn.setFixedSize(34, 28)
        self.min_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.min_btn.setStyleSheet(button_style)
        self.min_btn.clicked.connect(lambda: self.window().showMinimized())
        layout.addWidget(self.min_btn)

        # Maximize/Restore
        self.max_btn = QtWidgets.QPushButton("□")
        self.max_btn.setFixedSize(34, 28)
        self.max_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.max_btn.setStyleSheet(button_style)
        self.max_btn.clicked.connect(self.toggle_max_restore)
        layout.addWidget(self.max_btn)

        # Close (extra Farbe im Hover)
        self.close_btn = QtWidgets.QPushButton("×")
        self.close_btn.setFixedSize(34, 28)
        self.close_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: none;
                color: #ff3333;
                font-size: 22pt;
                border: 1.3px solid #555555;
                border-radius: 7px;
            }
            QPushButton:hover {
                color: #fff;
                background: #c80000;
                border-color: #ff3333;
            }
        """)
        self.close_btn.clicked.connect(lambda: self.window().close())
        layout.addWidget(self.close_btn)

        self._drag_pos = None

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

    def setTitle(self, text):
        self.title_label.setText(text)


class CustomDialog(QtWidgets.QDialog):
    def __init__(self, title="Dialog", parent=None):
        super().__init__(parent)
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

    def _resize_bg(self, event):
        self.bg_widget.setGeometry(self.rect())
        return super().resizeEvent(event)
