from PySide6 import QtWidgets, QtCore

APP_STYLESHEET = """
QWidget#customTitleBar QPushButton {
    color: #ffd600;
    background: #232323;
    border: none;
    border-radius: 16px;
    min-width: 40px;
    min-height: 40px;
    font-size: 20pt;
}
"""

class CustomTitleBar(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("customTitleBar")
        hbox = QtWidgets.QHBoxLayout(self)
        btn = QtWidgets.QPushButton("🗙")
        # KEIN eigenes setStyleSheet hier!
        hbox.addWidget(btn)
        hbox.addStretch()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)
    window = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(window)
    titlebar = CustomTitleBar()
    layout.addWidget(titlebar)
    window.resize(400, 200)
    window.show()
    app.exec()