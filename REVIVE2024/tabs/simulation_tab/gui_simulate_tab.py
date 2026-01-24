# native imports
import os
import psutil
import signal

# dependency imports
from PySide6.QtCore import (
    Qt,
    QTimer,
    Slot
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QLineEdit,
    QCheckBox,
    QProgressBar,
    QLabel, 
    QTableWidget,
    QTableWidgetItem
)
from PySide6.QtGui import QColor
import pandas as pd
import multiprocessing as mp

# custom imports
import tabs.simulation_tab.simulate as simulate
import misc.validation as validation
from gui_utility import *


class SimulateTab(QWidget):
    def __init__(self, parent):
        # init the widget
        super().__init__(parent)
        self.parent = parent

        # collect info from parent
        self.required_cols_file = self.parent.required_cols_file

        # create top-level widgets
        self.simulation_groupbox = QGroupBox("Simulation")
        self.review_groupbox = QGroupBox("Review")

        # dictionary for mapping titles to widgets for settings save
        self.file_entry_widgets = {}

        # populate groupboxes
        self.populate_simulation_groupbox()
        self.populate_review_groupbox()

        # add top-level widgets to main layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.simulation_groupbox)
        self.layout.addWidget(REVIVESpacer())
        self.layout.addWidget(self.review_groupbox)
        self.setLayout(self.layout)
        
        # initialize the threading mechanisms
        self.mp_manager = None
        self.progress_queue = None
        self.stop_event = None
        self.worker = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.query_progress)
        self.timer.start(500)


    def populate_simulation_groupbox(self):
        # create the new layout
        new_layout = QVBoxLayout()

        # establish labels
        self.file_entry_widget_labels = ["Batch Name",
                                         "IDD File Name",
                                         "Study/Output Folder",
                                         "Run List File",
                                         "Database Directory"]
        
        self.run_options_labels = ["Parallel Processes",
                                   "Generate PDF?",
                                   "Generate Graphs?",
                                   "Delete Unnecessary Files?"]

        # create the file entry widgets
        self.batch_name = QLineEdit()
        self.idd_file = REVIVEFilePicker(self.file_entry_widget_labels[1], "idd")
        self.study_folder = REVIVEFolderPicker(f"Select {self.file_entry_widget_labels[2]}")
        self.run_list_file = REVIVEFilePicker(self.file_entry_widget_labels[3], "csv")
        self.database_folder = REVIVEFolderPicker(f"Select {self.file_entry_widget_labels[4]}")

        file_entry_widget_list = [self.batch_name,
                                  self.idd_file,
                                  self.study_folder,
                                  self.run_list_file,
                                  self.database_folder]

        # assign keys to widgets for easy settings save and retrieve old settings
        for i, widget in enumerate(file_entry_widget_list):
            widget_key = self.file_entry_widget_labels[i]
            self.file_entry_widgets[widget_key] = widget
            if widget_key != self.file_entry_widget_labels[0]:
                widget.setText(self.parent.get_setting(widget_key))

        # create the run options widgets
        self.num_parallel_procs = REVIVEComboBox(items=[str(x) for x in [1,2,4,8,12,16,20,24,28,32]], add_null_item=False)
        self.gen_pdf_option = QCheckBox("Generate PDF?")
        self.gen_graphs_option = QCheckBox("Generate graphs?")
        self.del_files_option = QCheckBox("Delete unnecessary files?")
        
        # TODO: PDF GENERATION NOT YET IMPLEMENTED
        self.gen_pdf_option.setVisible(False)

        # build the left half with parallel process selection
        left_half = QVBoxLayout(alignment=Qt.AlignHCenter)
        left_half.addStretch()
        left_half.addWidget(QLabel("Parallel Processes"))
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
        run_options_layout = QHBoxLayout()
        run_options_layout.addLayout(left_half)
        run_options_layout.addLayout(right_half)

        # create simulation button widget
        self.sim_button = QPushButton("Simulate")
        self.sim_button.clicked.connect(self.simulate)

        # create progress bar widget
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0,100)
        self.progress_bar.reset()

        # add all new widgets to layout
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=file_entry_widget_list,
            label_list=self.file_entry_widget_labels
        ))
        new_layout.addWidget(REVIVESpacer())
        new_layout.addLayout(run_options_layout)
        new_layout.addWidget(REVIVESpacer())
        new_layout.addWidget(self.sim_button)
        new_layout.addWidget(self.progress_bar)
            
        # apply layout to groupbox widget
        self.simulation_groupbox.setLayout(new_layout)


    def populate_review_groupbox(self):
        # create new layout
        new_layout = QVBoxLayout()

        # create widgets
        self.results_file_label = QLabel("REVIVEcalc Results File:")
        self.results_file = REVIVEFilePicker("REVIVEcalc Results File", "csv")
        self.review_button = QPushButton(" Review Top Cases ")
        self.highlights_display = QTableWidget()

        # put widgets in a line
        review_line = QHBoxLayout()
        review_line.addWidget(self.results_file_label)
        review_line.addWidget(self.results_file)
        review_line.addWidget(self.review_button)
        self.review_widget = QWidget()
        self.review_widget.setLayout(review_line)

        # build table display widget
        self.num_top_cases = 5
        self.highlight_columns = ["Run Name", "SET ≤ 12.2°C Hours (F)", "Total Deadly Days", "EUI", "First Cost [$]", "Total ADORB Cost [$]"]
        self.display_columns = ["Case Name", "SET hours", "Deadly Days", "EUI", "First Cost", "Total ADORB Cost"]
        self.highlights_display.setRowCount(self.num_top_cases)
        self.highlights_display.setColumnCount(len(self.display_columns))
        self.highlights_display.setHorizontalHeaderLabels(self.display_columns)
        
        top_cases_layout = stack_widgets_horizontally(
            widget_list=[self.highlights_display],
            label_list=["Top Cases from Runlist"]
        )
        self.top_cases_widget = QWidget()
        self.top_cases_widget.setLayout(top_cases_layout)
        self.top_cases_widget.setVisible(False)

        # enable action to display content when selected
        self.review_button.clicked.connect(self.populate_highlights_table)

        # add widgets to main layout
        new_layout.addWidget(self.review_widget)

        # apply layout to groupbox widget
        self.review_groupbox.setLayout(new_layout)



    @Slot()
    def populate_highlights_table(self):
        # first clear the table
        self.highlights_display.clearContents()

        # collect results
        try:
            results_path = self.results_file.text()
            validation.validate_results_file(results_path, self.results_file_label.text()[:-1], self.highlight_columns)
            top_cases_df = simulate.ranked_top_cases(results_path, self.num_top_cases)
            
             # populate table
            for row_idx, row in top_cases_df.iterrows():
                for col_idx, col_key in enumerate(self.highlight_columns):
                    data = row[col_key]
                    item = QTableWidgetItem(str(data))
                    if row['Display Color']:
                        item.setBackground(QColor(row['Display Color']))
                    self.highlights_display.setItem(row_idx, col_idx, item)

            self.highlights_display.show()
            self.top_cases_widget.setWindowTitle("Result Review")
            self.top_cases_widget.resize(self.highlights_display.width(), 250)
            self.top_cases_widget.setVisible(True)

        except Exception as err:
            self.parent.display_error(str(err))
       

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
        idd_file = self.idd_file.text()
        study_folder = self.study_folder.text()
        run_list = self.run_list_file.text()
        db_dir = self.database_folder.text()
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