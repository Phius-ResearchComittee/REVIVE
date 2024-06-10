# native imports
import os
import psutil
import signal

# dependency imports
from PySide6.QtCore import (
    QDir,
    Qt,
    QTimer,
    Slot
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QPushButton,
    QLineEdit,
    QCheckBox,
    QComboBox,
    QProgressBar,
    QLabel,
    QStyle,
    QFileDialog
)
import pandas as pd
import multiprocessing as mp

# custom imports
import weatherMorph


class MorphTab(QWidget):
    def __init__(self, parent):
        # init the widget
        super().__init__(parent)
        self.parent = parent

        # create top-level widgets
        self.file_entry_layout = QGridLayout()
        self.file_entry_groupbox = QGroupBox("File Entry")
        self.run_options_layout = QHBoxLayout()
        self.run_options_groupbox = QGroupBox("Run Options")
        self.morph_button = QPushButton("Morph")
        self.progress_bar = QProgressBar()

        # create all inner-level widgets
        self.file_entry_widget = QLineEdit()

        # add top-level widgets to main layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.file_entry_groupbox)
        self.layout.addWidget(self.run_options_groupbox)
        self.layout.addWidget(self.morph_button)
        self.layout.addWidget(self.progress_bar)
        
        # populate the top-level widgets with child widgets
        self.create_file_entry_widgets()
        self.create_run_options_widgets()
        
        # enable the big simulate button
        self.morph_button.clicked.connect(self.morph)

        # initialize the progress bar attributes
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0,100)
        self.progress_bar.reset()

        # initialize the threading mechanisms
        self.mp_manager = None
        self.progress_queue = None
        self.stop_event = None
        self.worker = None
        
        # set the layout
        self.setLayout(self.layout)


    def create_file_entry_widgets(self):
        # show label and entry box
        self.file_label_string = "Input file"
        self.file_label = QLabel()
        self.file_label.setText(self.file_label_string)
        self.file_entry = QLineEdit()
        self.file_entry_layout.addWidget(self.file_label, 0, 0)
        self.file_entry_layout.addWidget(self.file_entry, 0, 1)

        # add file explorer widgets to layout
        self._open_file_explorer_action = self.file_entry.addAction(
                qApp.style().standardIcon(QStyle.SP_DirOpenIcon),  # noqa: F821
                QLineEdit.TrailingPosition)
            
        # populate fields with last used information, blank string as default
        self.file_entry.setText(self.parent.get_setting("Morph input"))

        # connect the actions
        self._open_file_explorer_action.triggered.connect( 
            lambda _ : self.on_open_file(self.file_label_string, "*.csv"))
            
        # apply layout to groupbox widget
        self.file_entry_groupbox.setLayout(self.file_entry_layout)

    
    def create_run_options_widgets(self):
        pass


    @Slot()
    def on_open_file(self, widget_key, file_ext):
        prompt = f"Select File: {widget_key}"
        
        path, _ = QFileDialog.getOpenFileName(
                self, prompt, QDir.homePath(), file_ext)

        dest = QDir(path)
        self.file_entry.setText(QDir.fromNativeSeparators(dest.path()))


    @Slot()
    def morph(self):
        # signal that simulation is starting (disable sim button)
        self.morph_button.setText("Running morph...")
        self.morph_button.setFlat(True)
        self.morph_button.setEnabled(False)

        # show the progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        try:
            # input validation
            err_string = "" # pass to input validation function here
            assert err_string == "", err_string

            # prepare inputs and save for next run
            self.save_settings()
            
            # collect arguments to send to simulate function
            morph_file = self.file_entry.text()

            #####################################################
            # Call morph function in weather morph here
            #####################################################
            print(f"Calling weather morph on file {morph_file}")

        
        except Exception as err_msg:
            self.morph_cleanup(success=False, err_msg=str(err_msg))

    
    def save_settings(self):
        self.parent.set_setting("Morph input", self.file_entry.text())
