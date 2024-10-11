# dependency imports
from PySide6.QtCore import (
    Slot
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QPushButton,
    QLineEdit,
)

# custom imports
import weatherMorph
from gui_utility import *


class MorphTab(QWidget):
    def __init__(self, parent):
        # init the widget
        super().__init__(parent)
        self.parent = parent

        # create top-level widgets
        self.settings_groupbox = QGroupBox("Site Weather Settings")
        self.morph_button = QPushButton("Compute Weather Morph Factors")

        # create all inner-level widgets
        self.file_entry_widget = QLineEdit()

        # add top-level widgets to main layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.settings_groupbox)
        self.layout.addWidget(self.morph_button)
        
        # populate the top-level widgets with child widgets
        self.create_widgets()
        
        # enable the big simulate button
        self.morph_button.clicked.connect(self.morph)
        
        # set the layout
        self.setLayout(self.layout)


    def create_widgets(self):
        # show input file box
        self.epw_csv_file = REVIVEFilePicker("EPW CSV File", "csv")
        self.summer_outage_start = REVIVEDatePicker()
        self.winter_outage_start = REVIVEDatePicker()
        self.summer_treturn_dp = REVIVEDoubleSpinBox(decimals=1, step_amt=0.1, min=-200, max=200)
        self.summer_treturn_db = REVIVEDoubleSpinBox(decimals=1, step_amt=0.1, min=-200, max=200)
        self.winter_treturn_dp = REVIVEDoubleSpinBox(decimals=1, step_amt=0.1, min=-200, max=200)
        self.winter_treturn_db = REVIVEDoubleSpinBox(decimals=1, step_amt=0.1, min=-200, max=200)

        # assign to layout
        new_layout = QVBoxLayout()
        new_layout.addLayout(stack_widgets_horizontally(
            widget_list=[self.epw_csv_file],
            label_list=["EPW CSV file"]
        ))
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=[self.winter_outage_start,
                         self.summer_outage_start],
            label_list=["Winter Outage Start",
                        "Summer Outage Start"]
        ))
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=[self.winter_treturn_dp,
                         self.winter_treturn_db,
                         self.summer_treturn_dp,
                         self.summer_treturn_db],
            label_list=["Winter Return Extreme Dew Point [°C]",
                        "Winter Return Extreme Dry Bulb [°C]",
                        "Summer Return Extreme Dew Point [°C]",
                        "Summer Return Extreme Dry Bulb [°C]"]
        ))
        self.settings_groupbox.setLayout(new_layout)


    @Slot()
    def morph(self):
        # signal that computation is starting (disable button)
        self.morph_button.setText("Computing morph factors...")
        self.morph_button.setFlat(True)
        self.morph_button.setEnabled(False)

        try:
            # input validation
            err_string = "" # pass to input validation function here
            assert err_string == "", err_string

            # prepare inputs and save for next run
            self.save_settings()
            
            # collect arguments to send to simulate function
            morph_file = self.epw_csv_file.text()
            summer_outage_start = self.summer_outage_start.get_date()
            winter_outage_start = self.winter_outage_start.get_date()
            summer_treturn_dp = self.summer_treturn_dp.value()
            summer_treturn_db = self.summer_treturn_db.value()
            winter_treturn_dp = self.winter_treturn_dp.value()
            winter_treturn_db = self.winter_treturn_db.value()

            print(f"Computing morph factors for EPW CSV file \"{morph_file}\"")
            summer_db_factor, summer_dp_factor, winter_db_factor, winter_dp_factor = weatherMorph.ComputeWeatherMorphFactors(
                morph_file, summer_outage_start, winter_outage_start, 
                summer_treturn_dp, summer_treturn_db, 
                winter_treturn_dp, winter_treturn_db
            )

            msg = (f"Morph factors calculation complete!\n"
                   f"MorphFactorDB1 = {winter_db_factor}\n"
                   f"MorphFactorDP1 = {winter_dp_factor}\n"
                   f"MorphFactorDB2 = {summer_db_factor}\n"
                   f"MorphFactorDP2 = {summer_dp_factor}\n")
            self.parent.display_info(msg)
            self.morph_cleanup(success=True)
        
        except Exception as err_msg:
            self.morph_cleanup(success=False, err_msg=str(err_msg))


    def morph_cleanup(self, success=False, err_msg=None):
        # notify the user
        if not success:
            self.parent.display_error(err_msg)

        # reset simulate button
        self.morph_button.setText("Compute Weather Morph Factors")
        self.morph_button.setFlat(False)
        self.morph_button.setEnabled(True)

    
    def save_settings(self):
        self.parent.set_setting("Morph input", self.epw_csv_file.text())
