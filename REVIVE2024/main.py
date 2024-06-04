
import sys
import gui
import multiprocessing as mp
from PySide6.QtWidgets import QApplication

if __name__=="__main__":
    mp.freeze_support()
    mp.set_start_method("spawn")
    app = QApplication([])

    widget = gui.MyWidget("-t" in sys.argv or "--test" in sys.argv)
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())