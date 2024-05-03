
import sys
import qt_gui as gui
from PySide6 import QtWidgets

if __name__=="__main__":
    app = QtWidgets.QApplication([])

    widget = gui.MyWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())