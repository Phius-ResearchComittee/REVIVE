from PySide6 import QtCore, QtWidgets, QtGui
import qt_simulate as simulate

class MyWidget(QtWidgets.QWidget):

    def __init__(self, is_dummy_mode: bool, parent: QtWidgets.QWidget=None):
        # initialize window
        super().__init__(parent)
        self.is_dummy_mode = is_dummy_mode

        # set up app identity
        self.app_name = "REVIVE Calculator Tool"
        self.settings = QtCore.QSettings("Phius", self.app_name)
        self.icon = QtGui.QIcon()
        self.icon.addFile("Phius-Logo-RGB__Color_Icon.ico")

        # customize window
        self.setWindowTitle(self.app_name)
        self.setWindowIcon(self.icon)

        # create a message box for error popups
        self.error_msg_box = QtWidgets.QMessageBox()
        self.error_msg_box.setIcon(QtWidgets.QMessageBox.Critical)
        self.error_msg_box.setWindowTitle("Error")
        self.error_msg_box.setWindowIcon(self.icon)

        # create a message box for completion alert
        self.info_msg_box = QtWidgets.QMessageBox()
        self.info_msg_box.setIcon(QtWidgets.QMessageBox.Information)
        self.info_msg_box.setWindowTitle(self.app_name)
        self.info_msg_box.setWindowIcon(self.icon)

        # create different pages
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.addTab(SimulateTab(self), "Simulation")
        self.tab_widget.addTab(MPAdorbTab(self), "Multi-phase ADORB")

        # attach tab widgets to main widget
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)


    def set_setting(self, setting_key, setting_val):
        self.settings.setValue(setting_key, setting_val)


    def get_setting(self, setting_key):
        return self.settings.value(setting_key, "")


    def display_error(self, msg: str):
        self.error_msg_box.setText(msg)
        self.error_msg_box.exec_()


    def display_info(self, msg: str):
        self.info_msg_box.setText(msg)
        self.info_msg_box.exec_()



class SimulateTab(QtWidgets.QWidget):
    def __init__(self, parent):
        # init the widget
        super().__init__(parent)
        self.parent = parent

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
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.file_entry_groupbox)
        self.layout.addWidget(self.run_options_groupbox)
        self.layout.addWidget(self.sim_button)
        
        # populate the top-level widgets with child widgets
        self.create_file_entry_widgets()
        self.create_run_options_widgets()
        
        # enable the big simulate button
        self.sim_button.clicked.connect(self.simulate)

        # set the layout
        self.setLayout(self.layout)


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
            qline.setText(self.parent.get_setting(widget_key))
            
            # add to layout
            qlabel = QtWidgets.QLabel()
            qlabel.setText(widget_key)
            self.file_entry_layout.addWidget(qlabel, i+1, 0)
            self.file_entry_layout.addWidget(qline, i+1, 1)

        # connect the actions
        self._open_file_explorer_actions[self.widget_labels[1]].triggered.connect( # IDD file
            lambda _ : self.on_open_file(self.widget_labels[1], "*.idd"))
        self._open_file_explorer_actions[self.widget_labels[2]].triggered.connect( # Study/output folder
            lambda _ : self.on_open_folder(self.widget_labels[2]))
        self._open_file_explorer_actions[self.widget_labels[3]].triggered.connect( # Run list file
            lambda _ : self.on_open_file(self.widget_labels[3], "*.csv"))
        self._open_file_explorer_actions[self.widget_labels[4]].triggered.connect( # Database folder
            lambda _ : self.on_open_folder(self.widget_labels[4]))
            
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
        # collect arguments to send to simulate function
        batch_name = self.batch_name.text()
        idd_file = self.file_entry_widgets[self.widget_labels[1]].text() # IDD File
        study_folder = self.file_entry_widgets[self.widget_labels[2]].text() # Study/output folder
        run_list = self.file_entry_widgets[self.widget_labels[3]].text() # Run list file
        db_dir = self.file_entry_widgets[self.widget_labels[4]].text() # Database directory
        show_graphs = self.gen_graphs_option.isChecked()
        gen_pdf_report = self.gen_pdf_option.isChecked()
        del_files = self.del_files_option.isChecked()

        # input validation
        err_string = simulate.validate_input(batch_name, idd_file, study_folder, run_list, db_dir)

        # run the simulation
        try:
            assert err_string == "", err_string
            self.save_settings() # remember these inputs for next run
            simulate.simulate(batch_name, idd_file, study_folder, run_list, db_dir, show_graphs, gen_pdf_report, self.parent.is_dummy_mode)
        except Exception as err_msg:
            self.parent.display_error(str(err_msg))
        else:
            self.parent.display_info("Analysis complete!")

    
    def save_settings(self):
        for widget_key, qline in self.file_entry_widgets.items():
            self.parent.set_setting(widget_key, qline.text())



class MPAdorbTab(QtWidgets.QWidget):
    def __init__(self, parent):
        
        # call widget init
        super().__init__()
        self.parent = parent

        # create top-level widgets
        self.layout = QtWidgets.QVBoxLayout()
        self.phases_layout = QtWidgets.QVBoxLayout()
        self.add_phase_button = QtWidgets.QPushButton("Add additional phase")
        self.complete_button = QtWidgets.QPushButton("Complete")

        # add widgets to main layout
        self.layout.addLayout(self.phases_layout)
        self.layout.addWidget(self.add_phase_button)
        self.layout.addStretch()
        self.layout.addWidget(self.complete_button)
        
        # init adorb constants
        self.phase_count = 1
        self.max_phases = 5
        self.num_sim_years = 70

        # store the results of the phases
        self.file_entries = {}
        self.year_entries = {}
        
        # set up phase entries
        for _ in range(3):
            self.spawn_phase_entry_widget()

        # enable the buttons
        self.add_phase_button.clicked.connect(self.spawn_phase_entry_widget)

        # set the layout
        self.setLayout(self.layout)


    @QtCore.Slot()
    def spawn_phase_entry_widget(self):
        # check to make sure we haven't exceded capacity
        if self.phase_count > self.max_phases:
            self.parent.display_error(f"Max number of phases reached: {self.max_phases}.")
            return

        # create box for labels, file entry, and year entry
        phase_layout = QtWidgets.QHBoxLayout()

        # create file entry box and connect action
        file_entry_box = QtWidgets.QLineEdit()
        self.file_entries[self.phase_count] = file_entry_box
        action = file_entry_box.addAction(
            qApp.style().standardIcon(QtWidgets.QStyle.SP_DirOpenIcon),  # noqa: F821
            QtWidgets.QLineEdit.TrailingPosition)
        action.triggered.connect(
            lambda _ : self.on_open_file(self.phase_count)
        )

        # create year dropdown box
        year_start_box = QtWidgets.QComboBox()
        year_start_box.addItems([str(x) for x in range(self.num_sim_years)])
        year_start_box.resize(200,100)
        self.year_entries[self.phase_count] = year_start_box

        # create labels
        file_entry_label = QtWidgets.QLabel("ADORB Results File:")
        year_start_label = QtWidgets.QLabel("Year:")

        # add new widgets to hbox
        phase_layout.addWidget(file_entry_label)
        phase_layout.addWidget(file_entry_box)
        phase_layout.addWidget(year_start_label)
        phase_layout.addWidget(year_start_box)

        new_phase_widget = QtWidgets.QGroupBox(f"Phase {self.phase_count}")
        new_phase_widget.setLayout(phase_layout)
        self.phases_layout.addWidget(new_phase_widget)
        self.phase_count += 1


    @QtCore.Slot()
    def on_open_file(self, phase_id):
        qline = self.file_entries[phase_id]
        prompt = f"Select File: Phase {phase_id}"
        
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, prompt, QtCore.QDir.homePath(), "*.csv")

        dest = QtCore.QDir(path)
        qline.setText(QtCore.QDir.fromNativeSeparators(dest.path()))