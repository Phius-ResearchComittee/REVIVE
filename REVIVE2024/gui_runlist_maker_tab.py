# native imports
import json

# dependency imports
import pandas as pd
from PySide6.QtCore import (
    Qt,
    Slot
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QCheckBox,
    QPushButton,
    QButtonGroup,
    QRadioButton
)

from gui_utility import *

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

        # create options source pane components
        self.use_phius_options_button = QRadioButton("Load PHIUS options")
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
            lambda _ : self.use_custom_options_button.setChecked(True))
        self.use_phius_options_button.setEnabled(True)
        self.refresh_options_button.clicked.connect(self.load_options_from_source)

        # add to options source layout
        self.options_pane = QVBoxLayout()
        self.options_pane.addWidget(self.use_phius_options_button)
        self.options_pane.addWidget(self.use_custom_options_button)
        self.options_pane.addWidget(self.custom_db_source)
        self.options_pane.addWidget(self.refresh_options_button)

        # create runlist export pane components
        self.create_new_rl_button = QRadioButton("Create New Runlist")
        self.create_new_rl_button.setChecked(True)
        self.new_runlist_file = REVIVEFilePicker("Save as:", parent=self.create_new_rl_button, file_ext="csv")
        self.add_existing_rl_button = QRadioButton("Add to Existing Runlist:")
        self.existing_runlist_file = REVIVEFilePicker("Select Runlist", parent=self.add_existing_rl_button, file_ext="csv")
        self.export_button = QPushButton("Export Case to Runlist")

        # group the runlist export radio buttons
        self.runlist_export = QButtonGroup()
        self.runlist_export.addButton(self.use_phius_options_button)
        self.runlist_export.addButton(self.use_custom_options_button)
        self.runlist_export.setExclusive(True)

        # connect runlist export pane components
        # self.create_new_rl_button.setChecked.connect(
        #     lambda _ : self.existing_runlist_file.setEnabled(False))
        # self.add_existing_rl_button.setChecked.connect(
        #     lambda _ : self.new_runlist_file.setEnabled(False))
        self.export_button.clicked.connect(self.export_to_csv)

        # build runlist export header
        self.export_pane = QVBoxLayout()
        self.export_pane.addWidget(self.create_new_rl_button)
        self.export_pane.addWidget(self.new_runlist_file)
        self.export_pane.addWidget(self.add_existing_rl_button)
        self.export_pane.addWidget(self.existing_runlist_file)
        self.export_pane.addWidget(self.export_button)

        # build content display widget
        self.case_builder = QWidget()
        self.case_builder_layout = QVBoxLayout(self.case_builder)
        self.scroll_area_label = QLabel("Case Builder")
        self.scroll_area_label.setAlignment(Qt.AlignCenter)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.case_builder)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMaximumWidth(QApplication.instance().primaryScreen().size().width()//2)

        # populate content 
        self.populate_groupboxes()
        self.populate_basic_groupbox()

        # enable action to display content when selected
        self.navigation_tree.itemSelectionChanged.connect(self.display_content)

        # build the rest of the maker layout
        self.maker_widget = QWidget()
        self.maker_layout = QVBoxLayout(self.maker_widget)
        self.maker_layout.addWidget(self.scroll_area_label)
        self.maker_layout.addWidget(self.scroll_area)

        # group the panes into groupboxes
        self.navigation_groupbox = QGroupBox("Navigation")
        self.navigation_groupbox.setLayout(self.navigation_pane)
        self.options_groupbox = QGroupBox("Runlist Options Source")
        self.options_groupbox.setLayout(self.options_pane)
        self.export_groupbox = QGroupBox("Export")
        self.export_groupbox.setLayout(self.export_pane)
        
        # build rest of the sidepane layout
        self.side_pane_widget = QWidget()
        self.side_pane_layout = QVBoxLayout(self.side_pane_widget)
        self.side_pane_layout.addWidget(self.navigation_groupbox)
        self.side_pane_layout.addWidget(self.options_groupbox)
        self.side_pane_layout.addWidget(self.export_groupbox)

        # add inner level widgets to horizontal layout
        self.split_layout.addWidget(self.side_pane_widget)
        self.split_layout.addWidget(self.maker_widget)

        # resize to maximize text display area
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
                                self.populate_outages_groupbox]
        
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
        new_layout.addLayout(self.stack_widgets_vertically(
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
        self.rl_morph_factors = [REVIVEDoubleSpinBox(decimals=2, step_amt=0.01, min=0, max=15) for _ in range(4)]
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
        new_layout.addLayout(self.stack_widgets_vertically(
            widget_list=[self.rl_epw_file,
                         self.rl_ddy_file],
            label_list=["EPW File",
                        "DDY File"]
        ))
        new_layout.addLayout(self.stack_widgets_vertically(
            widget_list=self.rl_morph_factors,
            label_list=["Morph Factor 1 - Dry Bulb (°C)",
                        "Morph Factor 1 - Dewpoint (°C)",
                        "Morph Factor 2 - Dry Bulb (°C)",
                        "Morph Factor 2 - Dewpoint (°C)"]
        ))
        new_layout.addLayout(self.stack_widgets_vertically(
            widget_list=[self.rl_env_country,
                         self.rl_grid_region,
                         self.rl_env_labor_frac],
            label_list=["Site Country",
                        "Grid Region",
                        "Envelope Labor Fraction"]
        ))
        new_layout.addLayout(self.stack_widgets_horizontally(
            widget_list=[self.rl_perf_carbon],
            label_list=["Performance Carbon Correction Measures"]
        ))
        new_layout.addLayout(self.stack_widgets_horizontally(
            widget_list=[self.rl_nperf_carbon],
            label_list=["Non-Performance Carbon Correction Measures"]
        ))

        # assign layout to groupbox
        self.assign_layout_to_groupbox(1, new_layout)

    def populate_energy_groupbox(self):
        # create the new form layout
        new_layout = QVBoxLayout()

        # create all the new widgets
        self.rl_elec_price = REVIVEDoubleSpinBox(decimals=2, step_amt=0.01, min=0, max=100)
        self.rl_elec_price.setPrefix("$")
        self.rl_elec_sellback_price = REVIVEDoubleSpinBox(decimals=2, step_amt=0.01, min=0, max=100)
        self.rl_elec_sellback_price.setPrefix("$")
        self.rl_nat_gas_present = QCheckBox()
        self.rl_nat_gas_present.setChecked(False)
        self.rl_nat_gas_price = REVIVEDoubleSpinBox(decimals=2, step_amt=0.01, min=0, max=100)
        self.rl_nat_gas_price.setPrefix("$")
        self.rl_nat_gas_price.setEnabled(False)
        self.rl_nat_gas_present.checkStateChanged.connect(
            lambda state : self.rl_nat_gas_price.setEnabled(state==Qt.Checked))
        self.rl_annual_gas_charge = REVIVESpinBox(step_amt=10)
        self.rl_annual_elec_charge = REVIVESpinBox(step_amt=10)

        # add all new widgets to layout with labels
        new_layout.addLayout(self.stack_widgets_vertically(
            widget_list=[self.rl_elec_price,
                         self.rl_elec_sellback_price,
                         self.rl_nat_gas_present,
                         self.rl_nat_gas_price],
            label_list=["Electric Price ($/kWh)",
                        "Electric Sellback Price ($/kWh)",
                        "Natural Gas Present?",
                        "Natural Gas Price ($/THERM)"]
        ))
        new_layout.addLayout(self.stack_widgets_vertically(
            widget_list=[self.rl_annual_gas_charge,
                         self.rl_annual_elec_charge],
            label_list=["Annual Gas Bill ($)",
                        "Annual Electric Bill ($)"]
        ))

        # assign layout to groupbox
        self.assign_layout_to_groupbox(2, new_layout)


    def populate_mechanicals_groupbox(self):
        # create the new form layout
        new_layout = QVBoxLayout()

        # create all the new widgets
        self.rl_mech_system = REVIVEComboBox() # TODO: SPLIT HEAT PUMP IN HVAC BUT NOT CONSTR. DB
        self.rl_water_heater_fuel = REVIVEComboBox()
        self.rl_pv_size = REVIVESpinBox(step_amt=500, min=0, max=12000)
        self.rl_pv_tilt = REVIVESpinBox(step_amt=10, min=0, max=90)
        self.appliance_list = ["Fridge","Dishwasher","Clotheswasher","Clothesdryer","Lights"]
        self.rl_appliances = [REVIVEComboBox() for _ in self.appliance_list]
        
        # add all new widgets to layout with labels
        new_layout.addLayout(self.stack_widgets_vertically(
            widget_list=[self.rl_mech_system,
                         self.rl_water_heater_fuel],
            label_list=["Mechanical System Type",
                        "Water Heater Fuel Type"]
        ))
        new_layout.addLayout(self.stack_widgets_horizontally(
            widget_list=[self.rl_pv_size,
                         self.rl_pv_tilt],
            label_list=["Photovoltaics Size (W)",
                        "Photovoltaics Tilt (deg)"]
        ))
        new_layout.addLayout(self.stack_widgets_vertically(
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
        self.rl_foundation_set = REVIVEFoundationWidgetSet(add_label="Add Foundation Layer", 
                                                           initial_widgets=1, 
                                                           max_widgets=3, 
                                                           label="Foundation Layer",
                                                           is_groupbox=True)
        self.rl_window_set = REVIVENameOnlyWidgetSet(add_label="Add Window Layer",
                                                     initial_widgets=1,
                                                     max_widgets=3,
                                                     label="Window Layer",
                                                     is_groupbox=True)
        self.rl_ext_door_set = REVIVENameOnlyWidgetSet(add_label="Add Exterior Door Layer",
                                                       initial_widgets=1,
                                                       max_widgets=3,
                                                       label="Ext. Door Layer",
                                                       is_groupbox=True)
        self.rl_ext_wall_set = REVIVENameOnlyWidgetSet(add_label="Add Exterior Wall Layer",
                                                       initial_widgets=1,
                                                       max_widgets=3,
                                                       label="Ext. Wall Layer",
                                                       is_groupbox=True)
        self.rl_ext_roof_set = REVIVENameOnlyWidgetSet(add_label="Add Roof Layer",
                                                       initial_widgets=1,
                                                       max_widgets=3,
                                                       label="Roof Layer",
                                                       is_groupbox=True)
        self.rl_ext_floor_set = REVIVENameOnlyWidgetSet(add_label="Add Exterior Floor Layer",
                                                       initial_widgets=1,
                                                       max_widgets=3,
                                                       label="Ext. Floor Layer",
                                                       is_groupbox=True)
        self.rl_int_floor_set = REVIVENameOnlyWidgetSet(add_label="Add Interior Floor Layer",
                                                       initial_widgets=1,
                                                       max_widgets=3,
                                                       label="Int. Floor Layer",
                                                       is_groupbox=True)

        # add all new widgets to layout with labels
        new_layout.addLayout(self.stack_widgets_vertically(
            widget_list=self.rl_op_areas,
            label_list=[f"Operable Area - {dir}" for dir in ["North", "East", "South", "West"]]
        ))
        self.revive_widget_sets = [self.rl_foundation_set, self.rl_window_set,
                              self.rl_ext_door_set, self.rl_ext_wall_set,
                              self.rl_ext_roof_set, self.rl_ext_floor_set,
                              self.rl_int_floor_set]
        self.envelope_items = ["Window", "Door", "Wall", "Roof", "Exterior Floor", "Interior Floor"]
        for w_set in self.revive_widget_sets:
            new_layout.addLayout(self.stack_widgets_horizontally(
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
        self.rl_nat_vent_type = REVIVEComboBox()
        self.rl_nat_vent_type.setEnabled(False)
        self.rl_nat_vent_avail.checkStateChanged.connect(
            lambda state : self.rl_nat_vent_type.setEnabled(state==Qt.Checked))

        # add all new widgets to layout with labels
        new_layout.addLayout(self.stack_widgets_vertically(
            widget_list=self.rl_outage_dates,
            label_list=["Winter Outage Start",
                        "Winter Outage End",
                        "Summer Outage Start",
                        "Summer Outage End"]
        ))
        new_layout.addLayout(self.stack_widgets_vertically(
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

    
    def assign_layout_to_groupbox(self, idx, new_layout):
        # get the group box from map earlier
        groupbox = self.category_to_groupbox_map[self.top_level_items[idx].text(0)]

        # assign layout to groupbox
        groupbox.setLayout(new_layout)

    
    def stack_widgets_vertically(self, widget_list, label_list):
        # organize the new layout
        new_layout = QFormLayout()
        new_layout.setLabelAlignment(Qt.AlignLeft)
        for widget, label in zip(widget_list, label_list):
            if label != "":
                label_widget = QLabel(f"{label}:")
                new_layout.addRow(label_widget, widget)
            else:
                new_layout.addWidget(widget)
        
        # return new layout with padding
        padded_layout = QVBoxLayout()
        padded_layout.addWidget(REVIVESpacer())
        padded_layout.addLayout(new_layout)
        padded_layout.addWidget(REVIVESpacer())
        return padded_layout
    

    def stack_widgets_horizontally(self, widget_list, label_list):
        # organize the new layout
        new_layout = QHBoxLayout()
        for widget, label in zip(widget_list, label_list):
            buddy_layout = QVBoxLayout()
            if label != "":
                label_widget = QLabel(f"{label}:")
                buddy_layout.addWidget(label_widget)
            if isinstance(widget, QWidget):
                buddy_layout.addWidget(widget)
            else:
                buddy_layout.addLayout(widget)
            new_layout.addLayout(buddy_layout)
        
        # return new layout with padding
        padded_layout = QVBoxLayout()
        padded_layout.addWidget(REVIVESpacer())
        padded_layout.addLayout(new_layout)
        padded_layout.addWidget(REVIVESpacer())
        return padded_layout
    
    
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
        self.runlist_dict["ELEC_PRICE_"] = self.rl_elec_price.cleanText()
        self.runlist_dict["SELLBACK_PRICE_[$/kWh]"] = self.rl_elec_sellback_price.cleanText()
        self.runlist_dict["NATURAL_GAS"] = self.rl_nat_gas_present.isChecked()
        self.runlist_dict["GAS_PRICE_[$/THERM]"] = self.rl_nat_gas_price.cleanText()
        self.runlist_dict["ANNUAL_GAS_CHARGE"] = self.rl_annual_gas_charge.cleanText()
        self.runlist_dict["ANNUAL_ELEC_CHARGE"] = self.rl_annual_elec_charge.cleanText()
        
        # mechanicals
        self.runlist_dict["MECH_SYSTEM_TYPE"] = self.rl_mech_system.currentText()
        self.runlist_dict["WATER_HEATER_FUEL"] = self.rl_water_heater_fuel.currentText()
        self.runlist_dict["PV_SIZE_[W]"] = self.rl_pv_size.cleanText()
        self.runlist_dict["PV_TILT"] = self.rl_pv_tilt.cleanText()
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
            for j, attr in enumerate(["INTERFACE", "INSUINSULATION"]):
                self.runlist_dict[f"FOUNDATION_{attr}_{i+1}"] = foundation_widgets[i][j].currentText() if i<len(foundation_widgets) else ""
            for j, attr in enumerate(["PERIMETER", "DEPTH"]):
                self.runlist_dict[f"FOUNDATION_{attr}_{i+1}"] = foundation_widgets[i][j].cleanText() if i<len(foundation_widgets) else ""
            
            # windows, walls, roofs, doors, floors
            self.runlist_dict[f"EXT_WINDOW_{i+1}"] = safe_get_element(i,windows)
            self.runlist_dict[f"EXT_WALL_{i+1}_NAME"] = safe_get_element(i,ext_walls)
            self.runlist_dict[f"EXT_ROOF_{i+1}_NAME"] = safe_get_element(i,ext_doors)
            self.runlist_dict[f"EXT_FLOOR_{i+1}_NAME"] = safe_get_element(i,ext_roofs)
            self.runlist_dict[f"EXT_DOOR_{i+1}_NAME"] = safe_get_element(i,ext_floors)
            self.runlist_dict[f"INT_FLOOR_{i+1}_NAME"] = safe_get_element(i,int_floors)

        
        # outages
        self.runlist_dict["1ST_OUTAGE"] = "HEATING"
        self.runlist_dict["OUTAGE_1_START"] = self.rl_outage_dates[0].get_date()
        self.runlist_dict["OUTAGE_1_END"] = self.rl_outage_dates[1].get_date()
        self.runlist_dict["OUTAGE_2_START"] = self.rl_outage_dates[2].get_date()
        self.runlist_dict["OUTAGE_2_END"] = self.rl_outage_dates[3].get_date()
        self.runlist_dict["NAT_VENT_AVAIL"] = self.rl_nat_vent_avail.isChecked()
        self.runlist_dict["NAT_VENT_TYPE"] = self.rl_nat_vent_type.currentText() if self.rl_nat_vent_avail.isChecked() else "NatVent"
        self.runlist_dict["SHADING_AVAIL"] = self.rl_shading_avail.isChecked()
        self.runlist_dict["DEMAND_COOLING_AVAIL"] = self.rl_dem_cool_avail.isChecked()

    
    @Slot()
    def load_options_from_source(self):
        # load from designated source
        try:
            if self.use_phius_options_button.isChecked():
                self.load_phius_runlist_options()
                prompt = "PHIUS runlist options loaded successfully!"
            else:
                self.load_custom_runlist_options()
                prompt = f"Custom runlist options from database folder \"{self.custom_db_source.text()}\" loaded successfully!"
                print("custom import not yet implemented")
                return
        except Exception as e:
            self.parent.display_error(str(e))
            return

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
        self.rl_nat_vent_type.change_items(self.runlist_options["Natural Ventilation Type"])

        # prompt user of success
        self.parent.display_info(prompt)


    def load_phius_runlist_options(self):
        with open(self.runlist_options_file, "r") as fp:
            self.runlist_options = json.load(fp)
    

    def load_custom_runlist_options(self):
        pass


    @Slot()
    def display_content(self):
        choice = self.navigation_tree.selectedItems()[0]
        parent = choice.parent()
        top_level = parent if parent is not None else choice
        category = top_level.text(0)
        groupbox = self.category_to_groupbox_map[category]
        ypos = groupbox.pos().y() - 10 # 10 for padding
        self.scroll_area.verticalScrollBar().setValue(ypos)    
    

    @Slot()
    def create_new_runlist(self):
        # get dict of current results
        self.collect_results()
        print(self.runlist_dict)


    @Slot()
    def add_to_runlist(self):
        # get dict of current results
        self.collect_results()
        
        # get current runlist
        df = pd.read_csv(self.existing_runlist)

        # simple validation
        assert set(df.columns)==set(self.runlist_dict.keys())

    @Slot()
    def export_to_csv(self):
        print("exporting not yet implemented")

