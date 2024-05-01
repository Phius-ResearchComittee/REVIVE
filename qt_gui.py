from PySide6 import QtCore, QtWidgets
import qt_simulate as simulate

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("REVIVE Calculator Tool")

        self.widget_labels = ["Batch Name",
                              "IDD File Name",
                              "Study/Output Folder",
                              "Run List File",
                              "Database Directory",
                              "Parallel Processes",
                              "Generate PDF?",
                              "Generate Graphs?",
                              "Delete Unnecessary Files?"]

        # create top-level widgets
        self.file_entry_layout = QtWidgets.QVBoxLayout()
        self.file_entry_groupbox = QtWidgets.QGroupBox("File Entry")
        self.run_options_layout = QtWidgets.QHBoxLayout()
        self.run_options_groupbox = QtWidgets.QGroupBox("Run Options")
        self.sim_button = QtWidgets.QPushButton("Simulate")

        # create all inner-level widgets
        self.batch_name = QtWidgets.QLineEdit()
        self.file_entry_widgets = {}
        for field in self.widget_labels[1:5]:
               self.file_entry_widgets[field] = QtWidgets.QLineEdit()
        self.gen_pdf_option = QtWidgets.QCheckBox()
        self.gen_graphs_option = QtWidgets.QCheckBox()
        self.del_files_option = QtWidgets.QCheckBox()
        self.num_parallel_procs = QtWidgets.QComboBox()
        self.progress_bar = QtWidgets.QProgressBar()

        # add top-level widgets to main layout
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.file_entry_groupbox)
        self.layout.addWidget(self.run_options_groupbox)
        self.layout.addWidget(self.sim_button)
        
        # populate the top-level widgets with child widgets
        self.create_file_entry_widgets()
        
        # enable the big simulate button
        self.sim_button.clicked.connect(self.simulate)


    def create_file_entry_widgets(self):
        # preface file entry area with batch name widget
        self.file_entry_layout.addWidget(self.batch_name)

        # add file explorer widgets to layout
        self._open_file_explorer_actions = {}
        for widget_key, qline in self.file_entry_widgets.items():

            # create the actions
            self._open_file_explorer_actions[widget_key] = qline.addAction(
                qApp.style().standardIcon(QtWidgets.QStyle.SP_DirOpenIcon),  # noqa: F821
                QtWidgets.QLineEdit.TrailingPosition)
            
            # add to layout
            self.file_entry_layout.addWidget(qline)

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