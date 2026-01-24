# native imports
import csv
import json
import os
# dependency imports
import pandas as pd

import eppy as eppy
from eppy import modeleditor
from eppy.modeleditor import IDF


from PySide6.QtCore import (
    Qt,
    Slot
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QCheckBox,
    QPushButton,
    QButtonGroup,
    QRadioButton,
    QMessageBox
)

from gui_utility import *
import misc.validation as validation

class RunlistMakerTab(QWidget):
    def __init__(self, parent):
        
        # call widget init
        super().__init__(parent)
        self.parent = parent
        # assign external content file handles
        self.help_tree_struc_file = parent.help_tree_struc_file
        self.help_content_file = parent.help_tree_content_file
        self.runlist_options_file = parent.runlist_ops_file
        self.required_cols_file = parent.required_cols_file
        
        # establish runlist options as empty to start
        self.runlist_options = {}
        # gemoetry options for geometry file operations
        self.geometry_options = {}
        
                
        # create top-level widgets
        self.layout = QVBoxLayout()
        self.split_layout = QHBoxLayout()

        # add widgets to main layout
        self.layout.addLayout(self.split_layout)
        
        # build content tree widget
        self.navigation_tree = REVIVEHelpTree()
        self.top_level_items, self.all_items = self.navigation_tree.populate_from_file(
            self.help_tree_struc_file)
        
        # add to navigation layout
        self.navigation_pane = QVBoxLayout()
        self.navigation_pane.addWidget(self.navigation_tree)
        #-------------------------------------------
        #RUNLIST OPTIONS SOURCE SECTION
        #---------------------------------------
        # create runlist options source pane components
        self.use_phius_options_button = QRadioButton("Load Phius options")
        self.use_phius_options_button.setChecked(True)
        self.use_custom_options_button = QRadioButton("Load custom options from database:")
        self.custom_db_source = REVIVEFolderPicker("Select Database Folder", parent=self.use_custom_options_button)
        self.refresh_options_button = QPushButton("Load Options into Runlist Maker")

        # group the options source radio buttons
        self.options_source_group = QButtonGroup()
        self.options_source_group.addButton(self.use_phius_options_button)
        self.options_source_group.addButton(self.use_custom_options_button)
        self.options_source_group.setExclusive(True)

        # connect options source pane components
        self.custom_db_source.textChanged.connect(
            lambda _ : self.use_custom_options_button.setChecked(True)
        )
        self.use_phius_options_button.setEnabled(True)
        self.refresh_options_button.clicked.connect(self.load_options_from_source)

        # add to options source layout
        self.options_pane = QVBoxLayout()
        self.options_pane.addWidget(self.use_phius_options_button)
        self.options_pane.addWidget(self.use_custom_options_button)
        self.options_pane.addWidget(self.custom_db_source)
        self.options_pane.addWidget(self.refresh_options_button)
        
        
        #------------------------------------------
        #geometry import,layout,connection code below
        #--------------------------------------------
        #geometry file components
     
        self.geometry_idf_file_source = REVIVEFilePicker("geometry file","idf")
        self.geometry_epw_file_source = REVIVEFilePicker("epw file","idd")
        self.import_geometry_button = QPushButton("Import geometry file")
        
        #geometry connection file
        self.geometry_idf_file_source.textChanged.connect(
            lambda _ : self.import_geometry_button.setChecked(True)
        )
        self.geometry_epw_file_source.textChanged.connect(
            lambda _ : self.import_geometry_button.setChecked(True)
        )
        self.import_geometry_button.clicked.connect(self.importZonesFromGeometry)
        
        #Geometry file pane layout
        self.geometry_pane = QVBoxLayout()
        self.geometry_pane.addWidget(self.geometry_idf_file_source)
        self.geometry_pane.addWidget(self.geometry_epw_file_source)
        self.geometry_pane.addWidget(self.import_geometry_button)
        
    
        
        #-----------------------------------------------
        # Export Runlist section
        #---------------------------------------------
        self.create_new_rl_button = QRadioButton("Create New Runlist")
        self.create_new_rl_button.setChecked(True)
        self.new_runlist_file = REVIVEFileSaver("Save as:", parent=self.create_new_rl_button)

        self.add_existing_rl_button = QRadioButton("Add to Existing Runlist:")
        self.existing_runlist_file = REVIVEFilePicker("Select Runlist", parent=self.add_existing_rl_button, file_ext="csv")
        self.existing_runlist_file.textChanged.connect(
            lambda _ : self.add_existing_rl_button.setChecked(True)
        )
        
        self.export_button = QPushButton("Export Case to Runlist")

        # group the runlist export radio buttons
        self.runlist_export = QButtonGroup()
        self.runlist_export.addButton(self.use_phius_options_button)
        self.runlist_export.addButton(self.use_custom_options_button)
        self.runlist_export.setExclusive(True)
        self.export_button.clicked.connect(self.export_to_csv)
        #------------------------------------------------------- 
        
        #--------------------------------------
        # Add the above sections to GUI, left 
        #--------------------------------------
        # build runlist export header
        self.export_pane = QVBoxLayout()
        self.export_pane.addWidget(self.create_new_rl_button)
        self.export_pane.addWidget(self.new_runlist_file)
        self.export_pane.addWidget(self.add_existing_rl_button)
        self.export_pane.addWidget(self.existing_runlist_file)
        self.export_pane.addWidget(self.export_button)
        
        #--------------------------------------
        # Add the above sections to GUI, right 
        #--------------------------------------
        # build content display widget
        self.case_builder = QWidget()
        self.case_builder_layout = QVBoxLayout(self.case_builder)
        self.scroll_area_label = QLabel("Case Builder")
        self.scroll_area_label.setAlignment(Qt.AlignCenter)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.case_builder)
        self.scroll_area.setWidgetResizable(True)

        # populate content 
        self.populate_groupboxes()

        # enable action to display content when selected
        self.navigation_tree.itemSelectionChanged.connect(self.display_content)

        # build the rest of the maker layout
        self.maker_widget = QWidget()
        self.maker_widget.setMaximumWidth(QApplication.instance().primaryScreen().size().width()//2)
        self.maker_layout = QVBoxLayout(self.maker_widget)
        self.maker_layout.addWidget(self.scroll_area_label)
        self.maker_layout.addWidget(self.scroll_area)

        #-------------------------------
        # GROUP THE PANES, left
        #--------------------------------
        # group the panes into groupboxes
        self.navigation_groupbox = QGroupBox("Navigation")
        self.navigation_groupbox.setLayout(self.navigation_pane)
        self.options_groupbox = QGroupBox("Runlist Options Source")
        self.options_groupbox.setLayout(self.options_pane)
        # self.runlist_populate_groupbox = QGroupBox("Runlist Options Source")
        # self.runlist_populate_groupbox.setLayout(self.runlist_pane)
        self.geometry_groupbox = QGroupBox("Import Geometry file")
        self.geometry_groupbox.setLayout(self.geometry_pane)
        self.export_groupbox = QGroupBox("Export")
        self.export_groupbox.setLayout(self.export_pane)
        
        # build rest of the sidepane layout
        self.side_pane_widget = QWidget()
        self.side_pane_widget.setMaximumHeight(QApplication.instance().primaryScreen().size().height())
        self.side_pane_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
        self.side_pane_layout = QVBoxLayout(self.side_pane_widget)
        self.side_pane_layout.addWidget(self.navigation_groupbox, stretch=1)
        self.side_pane_layout.addWidget(self.options_groupbox)
        # self.side_pane_layout.addWidget(self.runlist_populate_groupbox)
        self.side_pane_layout.addWidget(self.geometry_groupbox)
        self.side_pane_layout.addWidget(self.export_groupbox)

        # add inner level widgets to horizontal layout
        self.split_layout.addWidget(self.side_pane_widget)
        self.split_layout.addWidget(self.maker_widget)
        self.split_layout.setStretch(0,0)
        self.split_layout.setStretch(1,1)

        # set the layout
        self.setLayout(self.layout)

        # populate dictionary for runlist options
        self.runlist_dict = {}
    

    def populate_groupboxes(self):
        # NOTE: GROUPBOX LIST IS DEPENDENT ON TOP LEVEL ITEMS IN HELP TREE STRUCTURE, DO NOT EDIT
        self.populate_funcs =  [self.populate_basic_groupbox,
                                self.populate_site_utility_groupbox,
                                self.populate_energy_groupbox,
                                self.populate_mechanicals_groupbox,
                                self.populate_envelope_groupbox,
                                self.populate_outages_groupbox,
                                self.populate_geometry_groupbox]
        
        self.category_to_pos_map = {}
        self.category_to_groupbox_map = {}
        cumul_pos = 0
        for cat_widget, populate_func in zip(self.top_level_items, self.populate_funcs):
            cat = cat_widget.text(0)
            
            # record the position of the groupbox
            self.category_to_pos_map[cat] = cumul_pos

            # add groupbox to layout
            groupbox = REVIVECategoryGroupBox(cat, parent=self.scroll_area)
            self.category_to_groupbox_map[cat] = groupbox
            self.case_builder_layout.addWidget(groupbox)
            self.case_builder_layout.addWidget(REVIVESpacer())

            # fill in and advance cursor position
            populate_func()
            cumul_pos += groupbox.sizeHint().height()

            
    def populate_basic_groupbox(self):
        # create the new form layout
        new_layout = QVBoxLayout()
        
        # create all the new widgets
        self.rl_case_name = QLineEdit()
        self.rl_geom_file = REVIVEFilePicker("Geometry File", "idf")
        self.rl_sim_duration = REVIVESpinBox(step_amt=1, min=1, max=100)
        self.rl_sim_duration.setValue(50)
        
        # add all new widgets to layout with labels
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=[self.rl_case_name,
                         self.rl_geom_file,
                         self.rl_sim_duration],
            label_list=["Case Name",
                        "Geometry File",
                        "Simulation Duration (Years)",]
        ))

        # assign layout to groupbox
        self.assign_layout_to_groupbox(0, new_layout)


    def populate_site_utility_groupbox(self):
        # create the new form layout
        new_layout = QVBoxLayout()
        
        # create all the new widgets
        self.rl_epw_file = REVIVEFilePicker("EPW File", "epw")
        self.rl_ddy_file = REVIVEFilePicker("DDY File", "ddy")
        self.rl_morph_factors = [REVIVEDoubleSpinBox(decimals=2, step_amt=0.01, min=-20, max=20) for _ in range(4)]
        self.rl_env_country = REVIVEComboBox()
        self.rl_grid_region = REVIVEComboBox()
        self.rl_env_labor_frac = REVIVEDoubleSpinBox(decimals=2, step_amt=0.1, min=0, max=10)
        self.rl_perf_carbon = REVIVENameOnlyWidgetSet(add_label="Add Performance Carbon Correction",
                                                      initial_widgets=0,
                                                      max_widgets=10,
                                                      label="Carbon Correction",
                                                      is_groupbox=True)
        self.rl_nperf_carbon = REVIVENameOnlyWidgetSet(add_label="Add Non-Performance Carbon Correction",
                                                      initial_widgets=0,
                                                      max_widgets=10,
                                                      label="Carbon Correction",
                                                      is_groupbox=True)
        
        # add all new widgets to layout with labels
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=[self.rl_epw_file,
                         self.rl_ddy_file],
            label_list=["EPW File",
                        "DDY File"]
        ))
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=self.rl_morph_factors,
            label_list=["Morph Factor 1 - Dry Bulb [°C]",
                        "Morph Factor 1 - Dewpoint [°C]",
                        "Morph Factor 2 - Dry Bulb [°C]",
                        "Morph Factor 2 - Dewpoint [°C]"]
        ))
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=[self.rl_env_country,
                         self.rl_grid_region,
                         self.rl_env_labor_frac],
            label_list=["Site Country",
                        "Grid Region",
                        "Envelope Labor Fraction"]
        ))
        new_layout.addLayout(stack_widgets_horizontally(
            widget_list=[self.rl_perf_carbon],
            label_list=["Performance Carbon Correction Measures"]
        ))
        new_layout.addLayout(stack_widgets_horizontally(
            widget_list=[self.rl_nperf_carbon],
            label_list=["Non-Performance Carbon Correction Measures"]
        ))

        # assign layout to groupbox
        self.assign_layout_to_groupbox(1, new_layout)

    def populate_energy_groupbox(self):
        # create the new form layout
        new_layout = QVBoxLayout()

        # create all the new widgets
        self.rl_elec_price = REVIVEDoubleSpinBox(decimals=4, step_amt=0.01, min=0, max=100)
        self.rl_elec_price.setPrefix("$")
        self.rl_elec_sellback_price = REVIVEDoubleSpinBox(decimals=4, step_amt=0.01, min=0, max=100)
        self.rl_elec_sellback_price.setPrefix("$")
        self.rl_nat_gas_present = QCheckBox()
        self.rl_nat_gas_present.setChecked(False)
        self.rl_nat_gas_price = REVIVEDoubleSpinBox(decimals=4, step_amt=0.01, min=0, max=100)
        self.rl_nat_gas_price.setPrefix("$")
        self.rl_nat_gas_price.setEnabled(False)
        self.rl_nat_gas_present.checkStateChanged.connect(
            lambda state : self.rl_nat_gas_price.setEnabled(state==Qt.Checked))
        self.rl_annual_gas_charge = REVIVESpinBox(step_amt=10)
        self.rl_annual_gas_charge.setPrefix("$")        
        self.rl_annual_elec_charge = REVIVESpinBox(step_amt=10)
        self.rl_annual_elec_charge.setPrefix("$")

        # add all new widgets to layout with labels
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=[self.rl_elec_price,
                         self.rl_elec_sellback_price,
                         self.rl_nat_gas_present,
                         self.rl_nat_gas_price],
            label_list=["Electric Price [$/kWh]",
                        "Electric Sellback Price [$/kWh]",
                        "Natural Gas Present [Bool]",
                        "Natural Gas Price [$/THERM]"]
        ))
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=[self.rl_annual_gas_charge,
                         self.rl_annual_elec_charge],
            label_list=["Annual Gas Fixed Charge [$]",
                        "Annual Electric Fixed Charge [$]"]
        ))

        # assign layout to groupbox
        self.assign_layout_to_groupbox(2, new_layout)


    def populate_mechanicals_groupbox(self):
        # create the new form layout
        new_layout = QVBoxLayout()

        # create all the new widgets
        self.rl_mech_system = REVIVEComboBox()
        self.rl_water_heater_fuel = REVIVEComboBox()
        self.rl_vent_system = REVIVEComboBox(items=["Balanced", "Exhaust"])
        self.rl_erv_sense = REVIVEDoubleSpinBox(max=1)
        self.rl_erv_latent = REVIVEDoubleSpinBox(max=1)
        self.rl_heating_cop = REVIVEDoubleSpinBox(max=10)
        self.rl_cooling_cop = REVIVEDoubleSpinBox(max=10)
        self.rl_pv_size = REVIVESpinBox(step_amt=500)
        self.rl_pv_tilt = REVIVESpinBox(step_amt=10, min=0, max=90)
        self.rl_pv_azimuth = REVIVESpinBox(step_amt=10, max=360)
        self.appliance_list = ["Fridge","Dishwasher","Clotheswasher","Clothesdryer","Lights"]
        self.rl_appliances = [REVIVEComboBox() for _ in self.appliance_list]
        
        # add all new widgets to layout with labels
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=[self.rl_vent_system,
                         self.rl_water_heater_fuel,
                         self.rl_mech_system],
            label_list=["Ventilation System",
                        "Water Heater Fuel Type",
                        "Mechanical System Type"]
        ))
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=[self.rl_heating_cop,
                         self.rl_cooling_cop],
            label_list=["Coefficient of Performance (Heating)",
                        "Coefficient of Performance (Cooling)"]
        ))
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=[self.rl_erv_sense,
                         self.rl_erv_latent],
            label_list=["Sensible Recovery Efficiency",
                        "Latent Recover Efficiency"]
        ))
        new_layout.addLayout(stack_widgets_horizontally(
            widget_list=[self.rl_pv_size,
                         self.rl_pv_tilt,
                         self.rl_pv_azimuth],
            label_list=["Photovoltaics Size [W]",
                        "Photovoltaics Tilt [deg]",
                        "Photovoltaics Azimuth [deg]"]
        ))
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=self.rl_appliances,
            label_list=self.appliance_list
        ))
        
        # assign layout to groupbox
        self.assign_layout_to_groupbox(3, new_layout)


    def populate_envelope_groupbox(self):
        # create the new form layout
        new_layout = QVBoxLayout()

        # create all the new widgets
        self.rl_chi_val = REVIVEDoubleSpinBox(decimals=3, step_amt=0.001, max=5)
        self.rl_infil_rate = REVIVEDoubleSpinBox(decimals=3, step_amt=0.01, min=0, max=1)
        self.rl_op_areas = [REVIVESpinBox(step_amt=1) for _ in range(4)]
        self.rl_foundation_set = REVIVEFoundationWidgetSet(add_label="Add Foundation Type", 
                                                           initial_widgets=1, 
                                                           max_widgets=3, 
                                                           label="Foundation Type",
                                                           is_groupbox=True)
        self.rl_window_set = REVIVENameOnlyWidgetSet(add_label="Add Window Type",
                                                     initial_widgets=1,
                                                     max_widgets=3,
                                                     label="Window Type",
                                                     is_groupbox=True)
        self.rl_ext_door_set = REVIVENameOnlyWidgetSet(add_label="Add Exterior Door Type",
                                                       initial_widgets=1,
                                                       max_widgets=3,
                                                       label="Ext. Door Type",
                                                       is_groupbox=True)
        self.rl_ext_wall_set = REVIVENameOnlyWidgetSet(add_label="Add Exterior Wall Type",
                                                       initial_widgets=1,
                                                       max_widgets=3,
                                                       label="Ext. Wall Type",
                                                       is_groupbox=True)
        self.rl_ext_roof_set = REVIVENameOnlyWidgetSet(add_label="Add Roof Type",
                                                       initial_widgets=1,
                                                       max_widgets=3,
                                                       label="Roof Type",
                                                       is_groupbox=True)
        self.rl_ext_floor_set = REVIVENameOnlyWidgetSet(add_label="Add Exterior Floor Type",
                                                       initial_widgets=1,
                                                       max_widgets=3,
                                                       label="Ext. Floor Type",
                                                       is_groupbox=True)
        self.rl_int_floor_set = REVIVENameOnlyWidgetSet(add_label="Add Interior Floor Type",
                                                       initial_widgets=1,
                                                       max_widgets=3,
                                                       label="Int. Floor Type",
                                                       is_groupbox=True)

        # add all new widgets to layout with labels
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=self.rl_op_areas,
            label_list=[f"Operable Area [ft2] - {dir}" for dir in ["North", "East", "South", "West"]]
        ))
        new_layout.addLayout(stack_widgets_horizontally(
            widget_list=[self.rl_chi_val,
                         self.rl_infil_rate],
            label_list=["Chi Value [Btu/hr °F]",
                        "Infiltration Rate [CFM/sf @50 Pa]"]
        ))
        self.revive_widget_sets = [self.rl_foundation_set, self.rl_window_set,
                              self.rl_ext_door_set, self.rl_ext_wall_set,
                              self.rl_ext_roof_set, self.rl_ext_floor_set,
                              self.rl_int_floor_set]
        self.envelope_items = ["Window", "Exterior Door", "Exterior Wall", "Roof", "Exterior Floor", "Interior Floor"]
        for w_set in self.revive_widget_sets:
            new_layout.addLayout(stack_widgets_horizontally(
                widget_list=[w_set],
                label_list=[""]
            ))

        # assign layout to groupbox
        self.assign_layout_to_groupbox(4, new_layout)


    def populate_outages_groupbox(self):
        # create the new form layout
        new_layout = QVBoxLayout()

        # create all the new widgets
        self.rl_outage_dates = [REVIVEDatePicker() for _ in range(4)]
        self.rl_shading_avail = QCheckBox()
        self.rl_shading_avail.setChecked(False)
        self.rl_dem_cool_avail = QCheckBox()
        self.rl_dem_cool_avail.setChecked(False)
        self.rl_nat_vent_avail = QCheckBox()
        self.rl_nat_vent_avail.setChecked(False)
        self.rl_nat_vent_type = REVIVEComboBox(items=["NatVent","SchNatVent"])
        self.rl_nat_vent_type.setEnabled(False)
        self.rl_nat_vent_avail.checkStateChanged.connect(
            lambda state : self.rl_nat_vent_type.setEnabled(state==Qt.Checked))

        # add all new widgets to layout with labels
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=self.rl_outage_dates,
            label_list=["Winter Outage Start",
                        "Winter Outage End",
                        "Summer Outage Start",
                        "Summer Outage End"]
        ))
        new_layout.addLayout(stack_widgets_vertically(
            widget_list=[self.rl_shading_avail,
                         self.rl_dem_cool_avail,
                         self.rl_nat_vent_avail,
                         self.rl_nat_vent_type],
            label_list=["Shading Available?",
                        "Demand Cooling Available?",
                        "Natural Ventilation Available?",
                        "Natural Ventilation Type"]
        ))
        
        # assign layout to groupbox
        self.assign_layout_to_groupbox(5, new_layout)
    
    def populate_geometry_groupbox(self):
        new_layout = QVBoxLayout()
        
        #create all the new widgets
        self.rl_zone_set = REVIVEGeometryWidgetSet(label="Zone Config",initial_widgets=0)
        new_layout.addLayout(stack_widgets_horizontally(
            widget_list=[self.rl_zone_set],
            label_list=["Zones"]
        ))
        # assign layout to groupbox
        self.assign_layout_to_groupbox(6, new_layout)
        
    def assign_layout_to_groupbox(self, idx, new_layout):
        # get the group box from map earlier
        groupbox = self.category_to_groupbox_map[self.top_level_items[idx].text(0)]

        # assign layout to groupbox
        groupbox.setLayout(new_layout)
    
    
    def collect_results(self):
        # basic
        self.runlist_dict["CASE_NAME"] = self.rl_case_name.text()
        self.runlist_dict["GEOMETRY_IDF"] = self.rl_geom_file.text()
        self.runlist_dict["ANALYSIS_DURATION"] = self.rl_sim_duration.cleanText()

        # site and utility
        self.runlist_dict["EPW"] = self.rl_epw_file.text()
        self.runlist_dict["DDY"] = self.rl_ddy_file.text()
        self.runlist_dict["MorphFactorDB1"] = self.rl_morph_factors[0].cleanText()
        self.runlist_dict["MorphFactorDP1"] = self.rl_morph_factors[1].cleanText()
        self.runlist_dict["MorphFactorDB2"] = self.rl_morph_factors[2].cleanText()
        self.runlist_dict["MorphFactorDP2"] = self.rl_morph_factors[3].cleanText()
        self.runlist_dict["ENVELOPE_COUNTRY"] = self.rl_env_country.currentText()
        self.runlist_dict["GRID_REGION"] = self.rl_grid_region.currentText()
        self.runlist_dict["ENVELOPE_LABOR_FRACTION"] = self.rl_env_labor_frac.cleanText()
        self.runlist_dict["PERF_CARBON_MEASURES"] = ", ".join([pc.currentText() for pc in self.rl_perf_carbon])
        self.runlist_dict["NON_PERF_CARBON_MEASURES"] = ", ".join([npc.currentText() for npc in self.rl_nperf_carbon])

        # energy pricing
        self.runlist_dict["ELEC_PRICE_[$/kWh]"] = self.rl_elec_price.cleanText()
        self.runlist_dict["SELLBACK_PRICE_[$/kWh]"] = self.rl_elec_sellback_price.cleanText()
        self.runlist_dict["NATURAL_GAS"] = int(self.rl_nat_gas_present.isChecked())
        self.runlist_dict["GAS_PRICE_[$/THERM]"] = self.rl_nat_gas_price.cleanText()
        self.runlist_dict["ANNUAL_GAS_CHARGE"] = self.rl_annual_gas_charge.cleanText()
        self.runlist_dict["ANNUAL_ELEC_CHARGE"] = self.rl_annual_elec_charge.cleanText()
        
        # mechanicals
        self.runlist_dict["MECH_SYSTEM_TYPE"] = self.rl_mech_system.currentText()
        self.runlist_dict["WATER_HEATER_FUEL"] = ''.join(self.rl_water_heater_fuel.currentText().split('_')[1:])
        self.runlist_dict["VENT_SYSTEM_TYPE"] = self.rl_vent_system.currentText()
        self.runlist_dict["HEATING_COP"] = self.rl_heating_cop.cleanText()
        self.runlist_dict["COOLING_COP"] = self.rl_cooling_cop.cleanText()
        self.runlist_dict["SENSIBLE_RECOVERY_EFF"] = self.rl_erv_sense.cleanText()
        self.runlist_dict["LATENT_RECOVERY_EFF"] = self.rl_erv_latent.cleanText()
        self.runlist_dict["PV_SIZE_[W]"] = self.rl_pv_size.cleanText()
        self.runlist_dict["PV_TILT"] = self.rl_pv_tilt.cleanText()
        self.runlist_dict["PV_AZIMUTH"] = self.rl_pv_azimuth.cleanText()
        self.runlist_dict["APPLIANCE_LIST"] = ", ".join([x.currentText() for x in self.rl_appliances if x != ""])

        # envelope (top-levels)
        self.runlist_dict["INFILTRATION_RATE"] = self.rl_infil_rate.cleanText()
        self.runlist_dict["CHI_VALUE"] = self.rl_chi_val.cleanText()
        self.runlist_dict["Operable_Area_N"] = self.rl_op_areas[0].cleanText()
        self.runlist_dict["Operable_Area_E"] = self.rl_op_areas[1].cleanText()
        self.runlist_dict["Operable_Area_S"] = self.rl_op_areas[2].cleanText()
        self.runlist_dict["Operable_Area_W"] = self.rl_op_areas[3].cleanText()

        # envelope (child-levels)
        foundation_widgets = [fdn for fdn in self.rl_foundation_set]
        windows = [window.currentText() for window in self.rl_window_set]
        ext_walls = [e_wall.currentText() for e_wall in self.rl_ext_wall_set]
        ext_doors = [e_door.currentText() for e_door in self.rl_ext_door_set]
        ext_roofs = [e_roof.currentText() for e_roof in self.rl_ext_roof_set]
        ext_floors = [e_floor.currentText() for e_floor in self.rl_ext_floor_set]
        int_floors = [i_floor.currentText() for i_floor in self.rl_int_floor_set]

        safe_get_element = lambda idx, arr : arr[idx] if idx<len(arr) else ""
        for i in range(3):
            # foundations
            for j, attr in enumerate(["INTERFACE", "INSULATION", "PERIMETER", "INSULATION_DEPTH"]):
                if i<len(foundation_widgets):
                    self.runlist_dict[f"FOUNDATION_{attr}_{i+1}"] = foundation_widgets[i][j].currentText() if j < 2 else foundation_widgets[i][j].cleanText()
                else:
                    self.runlist_dict[f"FOUNDATION_{attr}_{i+1}"] = ""
            
            # windows, walls, roofs, doors, floors
            self.runlist_dict[f"EXT_WINDOW_{i+1}"] = safe_get_element(i,windows)
            self.runlist_dict[f"EXT_WALL_{i+1}_NAME"] = safe_get_element(i,ext_walls)
            self.runlist_dict[f"EXT_ROOF_{i+1}_NAME"] = safe_get_element(i,ext_roofs)
            self.runlist_dict[f"EXT_FLOOR_{i+1}_NAME"] = safe_get_element(i,ext_floors)
            self.runlist_dict[f"EXT_DOOR_{i+1}_NAME"] = safe_get_element(i,ext_doors)
            self.runlist_dict[f"INT_FLOOR_{i+1}_NAME"] = safe_get_element(i,int_floors)

        
        # outages
        self.runlist_dict["1ST_OUTAGE"] = "HEATING"
        self.runlist_dict["OUTAGE_1_START"] = self.rl_outage_dates[0].get_date()
        self.runlist_dict["OUTAGE_1_END"] = self.rl_outage_dates[1].get_date()
        self.runlist_dict["OUTAGE_2_START"] = self.rl_outage_dates[2].get_date()
        self.runlist_dict["OUTAGE_2_END"] = self.rl_outage_dates[3].get_date()
        self.runlist_dict["NAT_VENT_AVAIL"] = int(self.rl_nat_vent_avail.isChecked())
        self.runlist_dict["NAT_VENT_TYPE"] = self.rl_nat_vent_type.currentText() if self.rl_nat_vent_avail.isChecked() else "NatVent"
        self.runlist_dict["SHADING_AVAIL"] = int(self.rl_shading_avail.isChecked())
        self.runlist_dict["DEMAND_COOLING_AVAIL"] = int(self.rl_dem_cool_avail.isChecked())
        
        zones = self.rl_zone_set.get_data()
        #self.runlist_dict["ZONES"] = {f"Zone {i+1}": [json.dumps(zone)] for i, zone in enumerate(zones)}
        
        
        
        
    @Slot()
    def load_options_from_source(self):
        # load from designated source
        try:
            if self.use_phius_options_button.isChecked():
                self.load_phius_runlist_options()
                prompt = "Phius runlist options loaded successfully!"
            else:
                self.load_custom_runlist_options()
                prompt = f"Custom runlist options from database folder \"{self.custom_db_source.text()}\" loaded successfully!"
        
            # populate runlist option dictionary
            self.rl_env_country.change_items(self.runlist_options["Country"])
            self.rl_grid_region.change_items(self.runlist_options["Grid Region"])
            self.rl_perf_carbon.change_items(self.runlist_options["Performance Carbon Correction Measures"])
            self.rl_nperf_carbon.change_items(self.runlist_options["Non-Performance Carbon Correction Measures"])
            self.rl_mech_system.change_items(self.runlist_options["Mechanical System"])
            self.rl_water_heater_fuel.change_items(self.runlist_options["Water Heater Fuel"])
            self.rl_foundation_set.change_items(self.runlist_options["Envelope"]["Foundation Insulation"])
            appliance_dict = self.runlist_options["Appliances"]
            for i, app in enumerate(self.appliance_list):
                self.rl_appliances[i].change_items(appliance_dict[app])
            envelope_dict = self.runlist_options["Envelope"]
            for i, item in enumerate(self.envelope_items):
                self.revive_widget_sets[i+1].change_items(envelope_dict[item]) # +1 to skip foundation

        except Exception as e:
            self.parent.display_error(f"Failure to load options from database: {str(e)}")
            return
        
        # prompt user of success
        self.parent.display_info(prompt)


    def load_phius_runlist_options(self):
        # get from phius runlist options json
        with open(self.runlist_options_file, "r") as fp:
            self.runlist_options = json.load(fp)
    

    def load_custom_runlist_options(self):
        # get the file location from entry
        db_path = self.custom_db_source.text()

        # check that database is valid
        # validation.validate_database_content(self.required_cols_file, db_path)        

        ### CHANGE BELOW
        # load carbon corrections
        cc = pd.read_csv(os.path.join(db_path,"Carbon Correction Database.csv"))
        self.runlist_options["Performance Carbon Correction Measures"] = sorted(list(cc['Name'].unique()), key=str.casefold)

        # load country emission 
        country = pd.read_csv(os.path.join(db_path,"Country Emission Database.csv"))
        self.runlist_options["Country"] = sorted(list(country['COUNTRY'].unique()), key=str.casefold)

        # load hourly emission
        hourly_emission = pd.read_csv(os.path.join(db_path,"Hourly Emission Rates.csv"))
        self.runlist_options["Grid Region"] = sorted(hourly_emission.columns.tolist()[4:], key=str.casefold)
        
        # load nonperformance cc
        ncc = pd.read_csv(os.path.join(db_path,"Nonperformance Carbon Correction Database.csv"))
        self.runlist_options["Non-Performance Carbon Correction Measures"] = sorted(list(ncc['Name']), key=str.casefold)

        # load materials and construction
        construction_groups = {
            "Mechanical System": "Mechanical",
            "Water Heater Fuel": "DHW",
            "Appliances": ["Fridge", "Dishwasher", "Clotheswasher", "Clothesdryer", "Lights"],
            "Envelope": ["Foundation Insulation", "Window", "Exterior Door", "Exterior Wall", "Roof", "Exterior Floor", "Interior Floor"]
        }

        construction_df = pd.read_csv(os.path.join(db_path,"Construction Database.csv"))
        for group, types in construction_groups.items():
            if isinstance(types, list):
                self.runlist_options[group] = {key: sorted(list(construction_df[construction_df['Type'] == key]['Name'].unique()), key=str.casefold) for key in types}
            else:
                self.runlist_options[group] = sorted(list(construction_df[construction_df['Type'] == types]['Name'].unique()), key=str.casefold)

        material_df = pd.read_csv(os.path.join(db_path, "Material Database.csv"))
        self.runlist_options["Envelope"]['Foundation Insulation'] += sorted(list(material_df['NAME'].unique()), key=str.casefold)
        # change filepickers to open to database directory
        for filepicker in [self.rl_epw_file, self.rl_ddy_file]:
            filepicker.assign_default_directory(db_path)

    #--------------------------------------
    #geometry file import funtion
    #------------------------------------
    def importZonesFromGeometry(self):
        
        idfName = self.geometry_idf_file_source.get_filename()   # C:/EnergyPlusV9-5-0/ExampleFiles/MultiStory.idf
        iddName = self.geometry_epw_file_source.get_filename()   # C:/EnergyPlusV9-5-0/Energy+.idd
        if not idfName :
            QMessageBox.warning(self, "Missing File", "Please select geometry file.")
            return
        if not iddName:
            
            QMessageBox.warning(self, "Missing File", "Please select EPW file.")
            return
            
        IDF.setiddname(iddName)
        idf = IDF(idfName)

        zone_name_list = [str(zone.Name) for zone in idf.idfobjects["Zone"]]
        self.geometry_options["ZONES"] = zone_name_list
        # self.runlist_dict["ZONES"] = self.rl_zone_set.get_data()
        for name in zone_name_list:
            self.rl_zone_set.spawn_widget()
            latest_widget = self.rl_zone_set.all_widgets[-1]
            combo_boxes = latest_widget.findChildren(REVIVEComboBox)
            
            if combo_boxes:
                
                zone_name_combo = combo_boxes[0]
                zone_name_combo.change_items(zone_name_list)
                zone_name_combo.setCurrentText(name)
            
        
     
    def import_runlist_csv(self):
        path = self.runlist_import_from_csv_file_source.text()
        if not path:
            QMessageBox.warning(self, "Missing File", "Please select a runlist CSV file.")
            return

        try:
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read CSV: {e}")
            return

        if not rows:
            QMessageBox.warning(self, "No Data", "The selected CSV is empty.")
            return

    # For now just load the first row — can be expanded later
        self.populate_gui_from_runlist_row(rows[0])

   
        
    @Slot()
    def display_content(self):
        choice = self.navigation_tree.selectedItems()[0]
        parent = choice.parent()
        top_level = parent if parent is not None else choice
        category = top_level.text(0)
        groupbox = self.category_to_groupbox_map[category]
        ypos = groupbox.pos().y() - 10 # 10 for padding
        self.scroll_area.verticalScrollBar().setValue(ypos)    
    

    def ensure_list_values(self, dictionary):
        """Ensure all dictionary values are lists."""
        for key, value in dictionary.items():
            if not isinstance(value, (list, tuple, pd.Series)):
                dictionary[key] = [value]
            else:
                print(f"skipped item {key}")
        return dictionary
    
    
    @Slot()
    def export_to_csv(self):
        self.collect_results()
        runlist_dict = self.runlist_dict.copy()
        zone_data = self.rl_zone_set.get_data()

    # Flatten runlist_dict
        runlist_df = pd.DataFrame.from_dict(self.ensure_list_values(runlist_dict), orient="index").transpose()
        runlist_row = runlist_df.iloc[0].to_dict()
        flat_rows = []
        for zone_name, info in zone_data.items():
            window_areas = info.get("window_areas", {})
            row = { zone_name: {
            "Zone": zone_name,
            "zone_type": info.get("zone_type", ""),
            "mechanical_type": info.get("mechanical_type", ""),
            "#_occupants": info.get("#_occupants", ""),
            "exhaust_flow": info.get("exhaust_flow", ""),
            "supply_flow": info.get("supply_flow", ""),
            "chi": info.get("chi", ""),
            "Window_N": window_areas.get("North", 0),
             "Window_E": window_areas.get("East", 0), 
             "Window_W": window_areas.get("West", 0),
            "Window_S": window_areas.get("South", 0)       
        }
            }
            
            flat_rows.append(row)
         # Validate structure
        # validation.validate_runlist_structure(self.required_cols_file, file_path)   
        runlist_row["ZONES"] = json.dumps(flat_rows)
        
        df = pd.DataFrame([runlist_row])

        # Check if the user wants to create a new runlist or append to an existing one

        file_path = self.new_runlist_file.text() if self.create_new_rl_button.isChecked() else self.existing_runlist_file.text()
        if not file_path:
            self.parent.display_error("Please specify a valid file path.")
            return

        if self.add_existing_rl_button.isChecked():
            try:
                existing_df = pd.read_csv(file_path)

            # Validate structure
             #   validation.validate_runlist_structure(self.required_cols_file, file_path)

            # Append
                df = pd.concat([existing_df, df], ignore_index=True)

            except Exception as e:
                self.parent.display_error(f"Failed to read existing runlist: {e}")
                return

        try:
            df.to_csv(file_path, index=False)
            self.parent.display_info(f"Runlist exported to {file_path}")
        except Exception as e:
            self.parent.display_error(f"Failed to export data: {e}")
            return