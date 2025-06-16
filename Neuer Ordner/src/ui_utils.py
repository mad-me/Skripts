from PySide6 import QtWidgets

def center_window(widget):
    app = QtWidgets.QApplication.instance()
    screen = app.primaryScreen()
    screen_geo = screen.availableGeometry()
    win_geo = widget.frameGeometry()
    win_geo.moveCenter(screen_geo.center())
    widget.move(win_geo.topLeft())
