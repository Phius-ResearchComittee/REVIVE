# native imports
import os
import sys

# dependency imports
from PySide6.QtCore import (
    QSettings,
)
from PySide6.QtWidgets import (
    QWidget,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
)
from PySide6.QtGui import QIcon

# custom imports
import gui_simulate_tab
import gui_adorb_tab
import gui_help_tab
import gui_morph_tab
import gui_runlist_maker_tab

class MyWidget(QWidget):

    def __init__(self, is_dummy_mode: bool, parent: QWidget=None):
        # initialize windowf
        super().__init__(parent)
        self.is_dummy_mode = is_dummy_mode

        # set up app identity
        self.app_name = "REVIVEcalc"
        self.version_no = "24.2"
        self.settings = QSettings("Phius", self.app_name)
        self.curr_dir = os.getcwd()

        # set up persistent app resources for exe
        self.app_directory = getattr(sys, "_MEIPASS", self.curr_dir)
        self.icon_file = os.path.join(self.app_directory, "Phius-Logo-RGB__Color_Icon.ico")
        self.runlist_ops_file = os.path.join(self.app_directory, "phius_runlist_options.json")
        self.help_tree_struc_file = os.path.join(self.app_directory, "help_tree_structure.txt")
        self.help_tree_content_file = os.path.join(self.app_directory, "help_tree_content.json")
        self.required_cols_file = os.path.join(self.app_directory, "required_columns.json")

        # customize window
        self.icon = QIcon()
        self.icon.addFile(self.icon_file)
        self.setWindowTitle(f"{self.app_name} v{self.version_no}")
        self.setWindowIcon(self.icon)

        # create a message box for error popups
        self.error_msg_box = QMessageBox()
        self.error_msg_box.setIcon(QMessageBox.Critical)
        self.error_msg_box.setWindowTitle("Error")
        self.error_msg_box.setWindowIcon(self.icon)

        # create a message box for completion alert
        self.info_msg_box = QMessageBox()
        self.info_msg_box.setIcon(QMessageBox.Information)
        self.info_msg_box.setWindowTitle(self.app_name)
        self.info_msg_box.setWindowIcon(self.icon)

        # create different pages
        self.tab_widget = QTabWidget()
        self.help_tab = gui_help_tab.HelpTab(self)
        self.runlist_maker_tab = gui_runlist_maker_tab.RunlistMakerTab(self)
        self.sim_tab = gui_simulate_tab.SimulateTab(self)
        self.mp_adorb_tab = gui_adorb_tab.MPAdorbTab(self)
        self.morph_tab = gui_morph_tab.MorphTab(self)
        self.tab_widget.addTab(self.help_tab, "Help")
        self.tab_widget.addTab(self.runlist_maker_tab, "Runlist Maker")
        self.tab_widget.addTab(self.sim_tab, "Simulation")
        self.tab_widget.addTab(self.mp_adorb_tab, "Multi-phase ADORB")
        self.tab_widget.addTab(self.morph_tab, "Weather Morphing")

        # attach tab widgets to main widget
        self.layout = QVBoxLayout()
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


    def closeEvent(self, event):
        # shut down simulation tab if sim is running
        self.sim_tab.shutdown_simulation()

        # proceed with regular shutdown
        event.accept()
