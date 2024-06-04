# native imports
import os

# dependency imports
from PySide6.QtCore import (
    QDir,
    Qt,
    Slot
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QLineEdit,
    QComboBox,
    QLabel,
    QStyle,
    QFileDialog,
    QToolButton 
)

# custom imports
import adorb

class MPAdorbTab(QWidget):
    def __init__(self, parent):
        
        # call widget init
        super().__init__()
        self.parent = parent

        # create top-level widgets
        self.layout = QVBoxLayout()
        self.phases_layout = QVBoxLayout()
        self.add_phase_button = QPushButton("Add additional phase")
        self.compute_button = QPushButton("Compute Multiphase ADORB")

        # add widgets to main layout
        self.layout.addLayout(self.phases_layout)
        self.layout.addWidget(self.add_phase_button)
        self.layout.addStretch()
        self.layout.addWidget(self.compute_button)
        
        # init adorb constants
        self.phase_count = 1
        self.max_phases = 5
        self.num_sim_years = 70

        # store the results of the phases
        self.file_entries = []
        self.year_entries = []

        # keep track of current phase widgets
        self.phase_widgets = []
        
        # set up phase entries
        for _ in range(3):
            self.spawn_phase_entry_widget()

        # enable the buttons
        self.add_phase_button.clicked.connect(self.spawn_phase_entry_widget)
        self.compute_button.clicked.connect(self.compute_mp_adorb)

        # set the layout
        self.setLayout(self.layout)


    @Slot()
    def spawn_phase_entry_widget(self):
        # check to make sure we haven't exceded capacity
        if self.phase_count > self.max_phases:
            self.parent.display_error(f"Max number of phases reached: {self.max_phases}.")
            return

        # create box for labels, file entry, and year entry
        phase_layout = QHBoxLayout()

        # create file entry boxes
        file_entry_box = QLineEdit()
        self.file_entries.append(file_entry_box)

        # create year dropdown box
        year_start_box = QComboBox()
        year_start_box.addItems([str(x) for x in range(self.num_sim_years)])
        year_start_box.resize(200,100)
        self.year_entries.append(year_start_box)

        # create labels
        file_entry_label = QLabel("ADORB Results File:")
        year_start_label = QLabel("Year:")

        # create delete button
        del_button = QToolButton()
        icon = qApp.style().standardIcon(QStyle.SP_DialogDiscardButton)
        del_button.setIcon(icon)
        del_button.setAutoRaise(True)
        del_button.setToolButtonStyle(Qt.ToolButtonIconOnly)

        # add new widgets to hbox
        phase_layout.addWidget(file_entry_label)
        phase_layout.addWidget(file_entry_box)
        phase_layout.addWidget(year_start_label)
        phase_layout.addWidget(year_start_box)
        phase_layout.addWidget(del_button)

        # add to layout
        new_phase_widget = QGroupBox(f"Phase {self.phase_count}")
        new_phase_widget.setLayout(phase_layout)
        self.phases_layout.addWidget(new_phase_widget)
        self.phase_widgets.append(new_phase_widget)
        self.phase_count += 1
        
        # connect delete button
        del_button.clicked.connect(lambda _ : self.delete_phase_entry_widget(new_phase_widget))

        # connect browse files button
        action = file_entry_box.addAction(
            qApp.style().standardIcon(QStyle.SP_DirOpenIcon),  # noqa: F821
            QLineEdit.TrailingPosition)
        action.triggered.connect(
            lambda _ : self.on_open_file(new_phase_widget)
        )


    @Slot()
    def delete_phase_entry_widget(self, widget):
        # remove the widget from the window
        self.phases_layout.removeWidget(widget)
        widget.deleteLater()

        # decrement titles
        idx = self.phase_widgets.index(widget)
        for i in range(len(self.phase_widgets)-1, idx, -1):
            self.phase_widgets[i].setTitle(self.phase_widgets[i-1].title())
        
        # remove widget and entries from list
        self.phase_widgets.pop(idx)
        self.file_entries.pop(idx)
        self.year_entries.pop(idx)
        self.phase_count -= 1


    @Slot()
    def on_open_file(self, groupbox: QGroupBox):
        phase_id = self.phase_widgets.index(groupbox)
        qline = self.file_entries[phase_id]
        prompt = f"Select File: Phase {phase_id+1}"
        
        path, _ = QFileDialog.getOpenFileName(
                self, prompt, QDir.homePath(), "*.csv")

        dest = QDir(path)
        qline.setText(QDir.fromNativeSeparators(dest.path()))


    @Slot()
    def compute_mp_adorb(self):
        # collect arguments to send to simulate function
        adorb_paths = [x.text() for x in self.file_entries]
        year_starts = [int(x.currentText()) for x in self.year_entries]
        
        # input validation
        err_string = adorb.validate_input(adorb_paths, year_starts, self.num_sim_years)

        # run the computation
        try:
            assert err_string == "", err_string
            adorb.multiphaseADORB(adorb_paths, year_starts, self.num_sim_years)
        except Exception as err_msg:
            self.parent.display_error(str(err_msg))
        else:
            self.parent.display_info("Computation complete!")
        
        # return to the home directory
        os.chdir(self.parent.home_dir)