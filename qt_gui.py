from PySide6 import QtCore, QtWidgets, QtGui
import qt_simulate as simulate
import sys

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # set up app identity
        self.app_name = "REVIVE Calculator Tool"
        self.settings = QtCore.QSettings("Phius", self.app_name)
        self.icon = QtGui.QIcon()
        self.icon.addFile("Phius-Logo-RGB__Color_Icon.ico")

        # customize window
        self.setWindowTitle(self.app_name)
        self.setWindowIcon(self.icon)

        # create top-level widgets
        self.file_entry_layout = QtWidgets.QGridLayout()
        self.file_entry_groupbox = QtWidgets.QGroupBox("File Entry")
        self.run_options_layout = QtWidgets.QHBoxLayout()
        self.run_options_groupbox = QtWidgets.QGroupBox("Run Options")
        self.sim_button = QtWidgets.QPushButton("Simulate")

        # hard-code widget labels TODO: change this somehow?
        self.widget_labels = ["Batch Name",
                              "IDD File Name",
                              "Study/Output Folder",
                              "Run List File",
                              "Database Directory",
                              "Parallel Processes",
                              "Generate PDF?",
                              "Generate Graphs?",
                              "Delete Unnecessary Files?"]

        # create all inner-level widgets
        self.batch_name = QtWidgets.QLineEdit()
        self.file_entry_widgets = {}
        for field in self.widget_labels[1:5]:
            self.file_entry_widgets[field] = QtWidgets.QLineEdit()
        self.gen_pdf_option = QtWidgets.QCheckBox(self.widget_labels[6])
        self.gen_graphs_option = QtWidgets.QCheckBox(self.widget_labels[7])
        self.del_files_option = QtWidgets.QCheckBox(self.widget_labels[8])
        self.num_parallel_procs = QtWidgets.QComboBox()
        self.progress_bar = QtWidgets.QProgressBar()

        # add top-level widgets to main layout
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.file_entry_groupbox)
        self.layout.addWidget(self.run_options_groupbox)
        self.layout.addWidget(self.sim_button)
        
        # populate the top-level widgets with child widgets
        self.create_file_entry_widgets()
        self.create_run_options_widgets()
        
        # enable the big simulate button
        self.sim_button.clicked.connect(self.simulate)

        # create a message box for error popups
        self.error_msg_box = QtWidgets.QMessageBox()
        self.error_msg_box.setIcon(QtWidgets.QMessageBox.Critical)
        self.error_msg_box.setWindowTitle("Error")
        self.error_msg_box.setWindowIcon(self.icon)

        # create a message box for completion alert
        self.completion_msg_box = QtWidgets.QMessageBox()
        self.completion_msg_box.setIcon(QtWidgets.QMessageBox.Information)
        self.completion_msg_box.setWindowTitle(self.app_name)
        self.completion_msg_box.setWindowIcon(self.icon)


    def create_file_entry_widgets(self):
        # preface file entry area with batch name widget
        batch_label = QtWidgets.QLabel()
        batch_label.setText(self.widget_labels[0])
        self.file_entry_layout.addWidget(batch_label, 0, 0)
        self.file_entry_layout.addWidget(self.batch_name, 0, 1)

        # add file explorer widgets to layout
        self._open_file_explorer_actions = {}
        for i, (widget_key, qline) in enumerate(self.file_entry_widgets.items()):

            # create the actions
            self._open_file_explorer_actions[widget_key] = qline.addAction(
                qApp.style().standardIcon(QtWidgets.QStyle.SP_DirOpenIcon),  # noqa: F821
                QtWidgets.QLineEdit.TrailingPosition)
            
            # populate fields with last used information, blank string as default
            qline.setText(self.settings.value(widget_key, ""))
            
            # add to layout
            qlabel = QtWidgets.QLabel()
            qlabel.setText(widget_key)
            self.file_entry_layout.addWidget(qlabel, i+1, 0)
            self.file_entry_layout.addWidget(qline, i+1, 1)

        # connect the actions
        self._open_file_explorer_actions[self.widget_labels[1]].triggered.connect( # IDD file
            lambda idd_handler : self.on_open_file(self.widget_labels[1], "*.idd"))
        self._open_file_explorer_actions[self.widget_labels[2]].triggered.connect( # Study/output folder
            lambda output_handler : self.on_open_folder(self.widget_labels[2]))
        self._open_file_explorer_actions[self.widget_labels[3]].triggered.connect( # Run list file
            lambda runlist_handler : self.on_open_file(self.widget_labels[3], "*.csv"))
        self._open_file_explorer_actions[self.widget_labels[4]].triggered.connect( # Database folder
            lambda db_handler : self.on_open_folder(self.widget_labels[4]))
            
        # apply layout to groupbox widget
        self.file_entry_groupbox.setLayout(self.file_entry_layout)

    
    def create_run_options_widgets(self):
        # label and add option items for parallel processes
        qlabel = QtWidgets.QLabel()
        qlabel.setText(self.widget_labels[5]) # Parallel processes
        self.num_parallel_procs.addItems([str(x) for x in [1,2,4,8,12,16,20,24,28,32]])

        # build the left half with parallel process selection
        left_half = QtWidgets.QVBoxLayout(alignment=QtCore.Qt.AlignHCenter)
        left_half.addStretch()
        left_half.addWidget(qlabel)
        left_half.addWidget(self.num_parallel_procs)
        left_half.addStretch()

        # build the right half with with checkbox options
        right_half = QtWidgets.QVBoxLayout(alignment=QtCore.Qt.AlignHCenter)
        right_half.addStretch()
        right_half.addWidget(self.gen_pdf_option, QtCore.Qt.AlignHCenter)
        right_half.addWidget(self.gen_graphs_option, QtCore.Qt.AlignHCenter)
        right_half.addWidget(self.del_files_option, QtCore.Qt.AlignHCenter)
        right_half.addStretch()

        # incorporate both left and right halves
        self.run_options_layout.addLayout(left_half)
        self.run_options_layout.addLayout(right_half)

        # apply layout to groupbox widget
        self.run_options_groupbox.setLayout(self.run_options_layout)


    @QtCore.Slot()
    def on_open_folder(self, widget_key):
        qline = self.file_entry_widgets[widget_key]
        prompt = f"Select Folder: {widget_key}"
        
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, prompt, QtCore.QDir.homePath(), QtWidgets.QFileDialog.ShowDirsOnly
        )
        dest = QtCore.QDir(path)
        qline.setText(QtCore.QDir.fromNativeSeparators(dest.path()))


    @QtCore.Slot()
    def on_open_file(self, widget_key, file_ext):
        qline = self.file_entry_widgets[widget_key]
        prompt = f"Select File: {widget_key}"
        
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, prompt, QtCore.QDir.homePath(), file_ext)

        dest = QtCore.QDir(path)
        qline.setText(QtCore.QDir.fromNativeSeparators(dest.path()))


    @QtCore.Slot()
    def simulate(self):
        simulate.simulate()