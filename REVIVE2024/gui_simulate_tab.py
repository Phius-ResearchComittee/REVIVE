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
import simulate
import validation


class SimulateTab(QWidget):
    def __init__(self, parent):
        # init the widget
        super().__init__(parent)
        self.parent = parent

        # collect info from parent
        self.required_cols_file = self.parent.required_cols_file

        # create top-level widgets
        self.file_entry_layout = QGridLayout()
        self.file_entry_groupbox = QGroupBox("File Entry")
        self.run_options_layout = QHBoxLayout()
        self.run_options_groupbox = QGroupBox("Run Options")
        self.sim_button = QPushButton("Simulate")
        self.progress_bar = QProgressBar()

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
        self.batch_name = QLineEdit()
        self.file_entry_widgets = {}
        for field in self.widget_labels[1:5]:
            self.file_entry_widgets[field] = QLineEdit()
        self.gen_pdf_option = QCheckBox(self.widget_labels[6])
        self.gen_pdf_option.setVisible(False)
        self.gen_graphs_option = QCheckBox(self.widget_labels[7])
        self.del_files_option = QCheckBox(self.widget_labels[8])
        self.num_parallel_procs = QComboBox()

        # add top-level widgets to main layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.file_entry_groupbox)
        self.layout.addWidget(self.run_options_groupbox)
        self.layout.addWidget(self.sim_button)
        self.layout.addWidget(self.progress_bar)
        
        # populate the top-level widgets with child widgets
        self.create_file_entry_widgets()
        self.create_run_options_widgets()
        
        # enable the big simulate button
        self.sim_button.clicked.connect(self.simulate)

        # initialize the progress bar attributes
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0,100)
        self.progress_bar.reset()

        # initialize the threading mechanisms
        self.mp_manager = None
        self.progress_queue = None
        self.stop_event = None
        self.worker = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.query_progress)
        self.timer.start(500)
        
        # set the layout
        self.setLayout(self.layout)


    def create_file_entry_widgets(self):
        # preface file entry area with batch name widget
        batch_label = QLabel()
        batch_label.setText(self.widget_labels[0])
        self.file_entry_layout.addWidget(batch_label, 0, 0)
        self.file_entry_layout.addWidget(self.batch_name, 0, 1)

        # add file explorer widgets to layout
        self._open_file_explorer_actions = {}
        for i, (widget_key, qline) in enumerate(self.file_entry_widgets.items()):

            # create the actions
            self._open_file_explorer_actions[widget_key] = qline.addAction(
                qApp.style().standardIcon(QStyle.SP_DirOpenIcon),  # noqa: F821
                QLineEdit.TrailingPosition)
            
            # populate fields with last used information, blank string as default
            qline.setText(self.parent.get_setting(widget_key))
            
            # add to layout
            qlabel = QLabel()
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
        qlabel = QLabel()
        qlabel.setText(self.widget_labels[5]) # Parallel processes
        self.num_parallel_procs.addItems([str(x) for x in [1,2,4,8,12,16,20,24,28,32]])

        # build the left half with parallel process selection
        left_half = QVBoxLayout(alignment=Qt.AlignHCenter)
        left_half.addStretch()
        left_half.addWidget(qlabel)
        left_half.addWidget(self.num_parallel_procs)
        left_half.addStretch()

        # build the right half with with checkbox options
        right_half = QVBoxLayout(alignment=Qt.AlignHCenter)
        right_half.addStretch()
        right_half.addWidget(self.gen_pdf_option, Qt.AlignHCenter)
        right_half.addWidget(self.gen_graphs_option, Qt.AlignHCenter)
        right_half.addWidget(self.del_files_option, Qt.AlignHCenter)
        right_half.addStretch()

        # incorporate both left and right halves
        self.run_options_layout.addLayout(left_half)
        self.run_options_layout.addLayout(right_half)

        # apply layout to groupbox widget
        self.run_options_groupbox.setLayout(self.run_options_layout)


    @Slot()
    def on_open_folder(self, widget_key):
        qline = self.file_entry_widgets[widget_key]
        prompt = f"Select Folder: {widget_key}"
        
        path = QFileDialog.getExistingDirectory(
            self, prompt, QDir.homePath(), QFileDialog.ShowDirsOnly
        )
        dest = QDir(path)
        qline.setText(QDir.fromNativeSeparators(dest.path()))


    @Slot()
    def on_open_file(self, widget_key, file_ext):
        qline = self.file_entry_widgets[widget_key]
        prompt = f"Select File: {widget_key}"
        
        path, _ = QFileDialog.getOpenFileName(
                self, prompt, QDir.homePath(), file_ext)

        dest = QDir(path)
        qline.setText(QDir.fromNativeSeparators(dest.path()))


    @Slot()
    def query_progress(self):
        # check to make sure queue is ready
        if (self.mp_manager is None or 
            self.worker is None or
            self.progress_queue is None): 
            return

        # sim is still running
        if (self.worker.is_alive() or not self.progress_queue.empty()):
            # consume all messages in the queue
            while not self.progress_queue.empty():
                next_msg = self.progress_queue.get_nowait()
                try:
                    # accept the progress achieved in the checkpoint
                    progress_achieved = float(next_msg) * 100
                    self.progress += progress_achieved
                    self.progress_bar.setValue(int(self.progress))
                
                # err string detected
                except ValueError:
                    # empty the queue and break out of function
                    self.sim_cleanup(success=False, err_msg=next_msg)
                    break

        # sim is stopped and queue is empty 
        else:
            # get progress bar to 100
            self.progress_bar.setValue(100)

            # end the simulation
            self.sim_cleanup(success=True)

    @Slot()
    def simulate(self):
        # signal that simulation is starting (disable sim button)
        self.sim_button.setText("Running simulation...")
        self.sim_button.setFlat(True)
        self.sim_button.setEnabled(False)

        # show the progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        # collect arguments to send to simulate function
        batch_name = self.batch_name.text()
        idd_file = self.file_entry_widgets[self.widget_labels[1]].text() # IDD File
        study_folder = self.file_entry_widgets[self.widget_labels[2]].text() # Study/output folder
        run_list = self.file_entry_widgets[self.widget_labels[3]].text() # Run list file
        db_dir = self.file_entry_widgets[self.widget_labels[4]].text() # Database directory
        num_procs = int(self.num_parallel_procs.currentText())
        show_graphs = self.gen_graphs_option.isChecked()
        gen_pdf_report = self.gen_pdf_option.isChecked()
        del_files = self.del_files_option.isChecked()
        is_dummy_mode = self.parent.is_dummy_mode


        # begin the simulation
        try:
            # inpute validation
            validation.validate_simulation_inputs(batch_name, idd_file, study_folder, run_list, db_dir, self.required_cols_file)
            sim_inputs = simulate.SimInputs(batch_name, idd_file, study_folder, run_list, db_dir, num_procs, show_graphs, gen_pdf_report, del_files, is_dummy_mode)
            
            # save for next run
            self.save_settings()
            
            # call the simulation in thread
            self.sim_start(sim_inputs)
        
        except Exception as err_msg:
            self.sim_cleanup(success=False, err_msg=str(err_msg))

    
    def sim_start(self, sim_inputs):
        # create the simulation manager objects
        self.mp_manager = mp.Manager()
        self.progress = 0
        self.progress_queue = self.mp_manager.Queue()
        self.stop_event = self.mp_manager.Event()

        # determine total number of runs
        self.total_runs = pd.read_csv(sim_inputs.run_list).shape[0]

        # assign work to worker thread
        self.worker = mp.Process(target=simulate.parallel_simulate, 
                                 args=(sim_inputs, self.progress_queue, self.stop_event))
        
        # start the worker thread
        self.worker.start()
    
    
    def sim_cleanup(self, success=False, err_msg=""):
        # notify the user
        if success:
            self.parent.display_info("Analysis complete!")
        else:
            self.parent.display_error(err_msg)
        
        # see if all threads have finished (continue running if not)
        if self.worker is not None and self.worker.is_alive():
            return
        
        # clear the queue
        while self.progress_queue is not None and not self.progress_queue.empty():
            self.progress_queue.get_nowait()

        # collect child process
        if self.worker is not None:
            self.worker.join()
            self.worker = None

        # reset simulate button
        self.sim_button.setText("Simulate")
        self.sim_button.setFlat(False)
        self.sim_button.setEnabled(True)
        
        # reset progress bar
        self.progress_bar.reset()
        self.progress_bar.setVisible(False)
        
        # return to the home directory
        os.chdir(self.parent.app_directory)

    
    def save_settings(self):
        for widget_key, qline in self.file_entry_widgets.items():
            self.parent.set_setting(widget_key, qline.text())
    

    def shutdown_simulation(self):
         # first try to stop gracefully by sending signal
        if self.stop_event is not None:
            self.stop_event.set()
        
        # shut down the multiprocessing manager
        if self.mp_manager is not None:
            self.mp_manager.shutdown()
            self.mp_manager = None
                
        # attempt to wait on the stop signal to be received
        if self.worker is not None:
            print("Shutting down simulation worker...")
            self.worker.join(2)

            # force kill if not exited in a few seconds
            if self.worker.is_alive():
                print("Force terminating simulation worker...")
                for proc in psutil.process_iter():
                    if "energyplus" in proc.name():
                        os.kill(proc.pid, signal.SIGINT)
                self.worker.terminate()
                self.worker.join()