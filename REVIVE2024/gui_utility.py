from PySide6.QtCore import (
    QDate,
    Qt,
    QDir,
    Slot
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QSizePolicy,
    QFileDialog,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QGroupBox,
    QLabel,
    QStyle,
    QLineEdit,
    QToolButton,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem
)

import eppy as eppy
from eppy import modeleditor
from eppy.modeleditor import IDF

class REVIVEFilePicker(QLineEdit):
    def __init__(self, prompt: str, file_ext: str, parent=None):
        super().__init__(parent)
        
        self.prompt = f"Select File: {prompt}"
        self.file_ext = file_ext
        self.default_directory = QDir.homePath()

        self.action = self.addAction(
            qApp.style().standardIcon(QStyle.SP_DirOpenIcon),  # noqa: F821
            QLineEdit.TrailingPosition)
        self.action.triggered.connect(self.on_open_file)
         
    def assign_default_directory(self, path):
        self.default_directory = path   
    
    @Slot()
    def on_open_file(self):
        
        path, _ = QFileDialog.getOpenFileName(
                self, self.prompt, self.default_directory, f"*.{self.file_ext}")

        dest = QDir(path)
        self.setText(QDir.fromNativeSeparators(dest.path()))


class REVIVEFolderPicker(QLineEdit):
    def __init__(self, prompt: str, parent=None):
        super().__init__(parent)

        self.prompt = prompt
        self.default_directory = QDir.homePath()

        self.action = self.addAction(
            qApp.style().standardIcon(QStyle.SP_DirOpenIcon),  # noqa: F821
            QLineEdit.TrailingPosition)
        self.action.triggered.connect(self.on_open_folder)
    
    def assign_default_directory(self, path):
        print(path)
        self.default_directory = path
    
    @Slot()
    def on_open_folder(self):
        
        path = QFileDialog.getExistingDirectory(
            self, self.prompt, self.default_directory, QFileDialog.ShowDirsOnly
        )
        dest = QDir(path)
        self.setText(QDir.fromNativeSeparators(dest.path()))

#Added FileSaver class
class REVIVEFileSaver(QLineEdit):
    def __init__(self, prompt: str, parent=None):
        super().__init__(parent)

        action = self.addAction(
            qApp.style().standardIcon(QStyle.SP_DirOpenIcon),  # noqa: F821
            QLineEdit.TrailingPosition)
        action.triggered.connect(
            lambda _ : self.on_save_file(prompt)
        )
    
    @Slot()
    def on_save_file(self, prompt: str):
        
        path, _ = QFileDialog.getSaveFileName(
            self, prompt, QDir.homePath(), "*.csv"
        )
        dest = QDir(path)
        self.setText(QDir.fromNativeSeparators(dest.path()))
        
class REVIVEHelpTree(QTreeWidget):
    def __init__(self, parent=None):
        # create the regular tree widget
        super().__init__(parent)

        # customize for table of contents
        self.setColumnCount(1)
        self.setHeaderHidden(True)
    
    def populate_from_file(self, file):
        top_level_items = []
        all_items = [] # items to be tuple of (item, level)
        with open(file, "r") as reader:
            for line in reader:
                # find the beginning of the word
                level = 0
                while line[level] == "-": level += 1

                # create the tree widget item
                name = line[level:].strip()
                tree_item = QTreeWidgetItem([name])

                # add to list of tree item list
                all_items.append((tree_item, level))

                # find parent topic if child topic
                if level > 0:
                    parent_level = level-1

                    # iterate through all items backwards to find most recent
                    for i in range(1,len(all_items)+1):
                        curr_item = all_items[-i]
                        
                        # check if the current item is the target level
                        if curr_item[1] == parent_level:
                            curr_item[0].addChild(tree_item)
                            break
                
                # if topic has no parent add to top level items
                else:
                    top_level_items.append(tree_item)

        # place top level items in tree
        self.insertTopLevelItems(0, top_level_items)

        # return list of top level items and all items
        return top_level_items, all_items


class REVIVESpinBox(QSpinBox):
    def __init__(self, step_amt=1, min=0, max=100_000_000, parent=None):
        # create the regular spinbox
        super().__init__(parent)

        # disable wheel scrolling
        self.wheelEvent = lambda event : event.ignore()

        # set parameters
        self.setSingleStep(step_amt)
        self.setRange(min, max)


class REVIVEDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, decimals=None, step_amt=0.01, min=0, max=100_000_000, parent=None):
        # create the regular spinbox
        super().__init__(parent)

        # disable wheel scrolling
        self.wheelEvent = lambda event : event.ignore()

        # set parameters
        if decimals is not None:
            self.setDecimals(decimals)
        self.setSingleStep(step_amt)
        self.setRange(min, max)


class REVIVEComboBox(QComboBox):
    def __init__(self, items=[], add_null_item=True, parent=None):
        # create the regular combobox
        super().__init__(parent)

        # disable wheel scrolling
        self.wheelEvent = lambda event : event.ignore()

        # add null item
        self.null_item = add_null_item
        if self.null_item:
            self.addItem("")

        # add actual items
        if items:
            self.addItems([str(item) for item in items])
    
    def change_items(self, new_items=[]):
        # rebuild the list of items
        self.clear()
        if self.null_item:
            self.addItem("")
        self.addItems(new_items)


class REVIVECategoryGroupBox(QGroupBox):
    pass


class REVIVEDatePicker(QWidget):
    def __init__(self, parent=None):
        # create the regular widget
        super().__init__(parent)

        # create the month and day pickers
        self.all_months = [QDate(1900, m+1, 1) for m in range(12)]
        self.month_picker = REVIVEComboBox(items=[date.toString("MMMM") for date in self.all_months],
                                           add_null_item=False)
        self.day_picker = REVIVEComboBox(items=[*range(1,32)], add_null_item=False)
        self.day_picker.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        # connect a signal to change number of days on month change
        self.month_picker.currentIndexChanged.connect(self.new_month_selected)

        # pair the month and day picker horizontally
        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(self.month_picker)
        self.hlayout.addWidget(self.day_picker)
        self.setLayout(self.hlayout)

    @Slot()
    def new_month_selected(self):
        # erase all existing day choices
        self.day_picker.clear()

        # get number of days for new month
        if self.month_picker.currentIndex() != -1:
            num_days = self.all_months[self.month_picker.currentIndex()].daysInMonth()
        
        # assign to day picker combobox
        self.day_picker.addItems([str(x+1) for x in range(num_days)])
    
    def get_date(self):
        month = self.month_picker.currentText()
        day = self.day_picker.currentText()
        return QDate.fromString(f"{month} {day}", "MMMM d").toString("d-MMM")


class REVIVEDeletableWidgetSet(QVBoxLayout):
    def __init__(self, add_label="Add", initial_widgets=1, max_widgets=5, label="", is_groupbox=False, parent=None):
        super().__init__(parent)

        self.widget_layout = QVBoxLayout()
        self.all_widgets = []
        self.max_widgets = max_widgets
        self.add_button = QPushButton(add_label)
        self.label_fn = lambda x : f"{label} {x+1}"
        self.labels = []
        self.is_groupbox = is_groupbox

        # create initial widgets
        for _ in range(initial_widgets):
            self.spawn_widget()
        
        # connect the add button
        self.add_button.clicked.connect(self.spawn_widget)

        self.addLayout(self.widget_layout)
        self.addWidget(self.add_button)

    def create_widget(self):
        return QWidget()

    @Slot()
    def spawn_widget(self):
        # create box for labels, file entry, and year entry
        item_layout = QHBoxLayout()

        # create delete button
        del_button = QToolButton()
        icon = qApp.style().standardIcon(QStyle.SP_DialogDiscardButton)
        del_button.setIcon(icon)
        del_button.setAutoRaise(True)
        del_button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        
        # add new widgets to hbox
        item_layout.addWidget(self.create_widget())
        item_layout.addWidget(del_button)

        # encapsulate in groupbox if specified
        if self.is_groupbox:
            new_group_widget = QGroupBox(self.label_fn(len(self.all_widgets)))
        else:
            new_group_widget = QWidget()
            new_label = QLabel(self.label_fn(len(self.all_widgets)))
            self.labels.append(new_label)
            item_layout.insertWidget(0, new_label)

        # put all items into a sole widget
        new_group_widget.setLayout(item_layout)
        
        # connect delete button
        del_button.clicked.connect(lambda _ : self.delete_widget(new_group_widget))

        # add to the layout and widget list
        self.widget_layout.addWidget(new_group_widget)
        self.all_widgets.append(new_group_widget)

        # disable add button if at max capacity
        if len(self.all_widgets) == self.max_widgets:
            self.add_button.setEnabled(False)


    @Slot()
    def delete_widget(self, widget):
        # remove the widget from the window
        self.widget_layout.removeWidget(widget)
        widget.deleteLater()

        # delete from widget list
        idx = self.all_widgets.index(widget)
        self.all_widgets.pop(idx)

        for i in range(idx, len(self.all_widgets)):
            new_label = self.label_fn(i)
            if self.is_groupbox:
                self.all_widgets[i].setTitle(new_label)
            else:
                self.labels[i].setText(new_label)
        
        # add button is enabled again after space cleared
        self.add_button.setEnabled(True)
    
    def __iter__(self):
        for x in self.all_widgets:
            yield x


class REVIVENameOnlyWidgetSet(REVIVEDeletableWidgetSet):
    def __init__(self, add_label="Add", initial_widgets=1, max_widgets=5, label="", is_groupbox=False, parent=None):
        self.choices = []
        super().__init__(add_label, initial_widgets, max_widgets, label, is_groupbox)
    
    def create_widget(self):
        widget = QWidget()
        hbox = QHBoxLayout()

        # create label and widget
        label = QLabel("Name:")
        combobox = REVIVEComboBox(parent=widget)
        combobox.change_items(self.choices)

        # add to layout
        hbox.addWidget(label)
        hbox.addWidget(combobox)

        # return new combined widget
        widget.setLayout(hbox)
        return widget
    
    def change_items(self, choices):
        self.choices = choices
        for x in self:
            x.change_items(self.choices)
    
    def __iter__(self):
        for x in super().__iter__():
            name_widg = x.findChildren(REVIVEComboBox)[0]
            yield name_widg

class REVIVEZoneWidgetSet(REVIVEDeletableWidgetSet):
    def __init__(self, add_label="Add", initial_widgets=1, max_widgets=100, label="", is_groupbox=False, parent=None):
        self.choices = []
        super().__init__(add_label, initial_widgets, max_widgets, label, is_groupbox)
    
        # self.load_zones_from_geometry_button = QPushButton("Load Zones from Geometry")
        # self.options_pane.addWidget(self.load_zones_from_geometry_button)

        
        # self.load_zones_from_geometry_button.clicked.connect(self.load_zones_from_geometry)

        # def load_zones_from_geometry(self):
        #     self.rl_zone_name_choice = []
        #     # get from phius runlist options json
        #     geometry_path = self.rl_geom_file.text()
        #     IDF.setiddname(self.idd_file.text())
        #     zone_list = []
        #     idfg = IDF(geometry_path)
        #     for zone in idfg.idfobjects['Zone']:
        #         zone_list.append(zone.Name)
        # # self.rl_zone_name_choice.change_items(zone_list)
    # working

        zone_widget = QWidget()
        zone_hbox = QHBoxLayout()

        # create interface vbox
        zone_name_vbox = QVBoxLayout()
        zone_name_label = QLabel("Zone Name")
        zone_name_choice = REVIVEComboBox(items=["UNIT", "CORRIDOR", "STAIR"])
        zone_name_choice.change_items(self.choices)

        zone_name_vbox.addWidget(zone_name_label)
        zone_name_vbox.addWidget(zone_name_choice)

        # create interface vbox
        zone_vbox = QVBoxLayout()
        zone_label = QLabel("Zone Type")
        zone_choice = REVIVEComboBox(items=["UNIT", "CORRIDOR", "STAIR"],
                                          parent=zone_widget)
        zone_vbox.addWidget(zone_label)
        zone_vbox.addWidget(zone_choice)


        # create bedroom - occupancy vbox
        bedroom_occupancy_vbox = QVBoxLayout()
        bedroom_occupancy_label = QLabel("Number of Beds / Occ")
        bedroom_occupancy_choice = REVIVESpinBox(parent=zone_widget)
        bedroom_occupancy_vbox.addWidget(bedroom_occupancy_label)
        bedroom_occupancy_vbox.addWidget(bedroom_occupancy_choice)

        # create chi vbox
        chi_vbox = QVBoxLayout()
        chi_label = QLabel("Chi Value [Btu/hr °F]")
        chi_choice = REVIVEDoubleSpinBox(parent=zone_widget)
        chi_vbox.addWidget(chi_label)
        chi_vbox.addWidget(chi_choice)

        # create operable_area_N vbox
        operable_area_N_vbox = QVBoxLayout()
        operable_area_N_label = QLabel("N Op. Window Area [ft2]")
        operable_area_N_choice = REVIVEDoubleSpinBox(parent=zone_widget)
        operable_area_N_vbox.addWidget(operable_area_N_label)
        operable_area_N_vbox.addWidget(operable_area_N_choice)

        # create operable_area_W vbox
        operable_area_W_vbox = QVBoxLayout()
        operable_area_W_label = QLabel("W Op. Window Area [ft2]")
        operable_area_W_choice = REVIVEDoubleSpinBox(parent=zone_widget)
        operable_area_W_vbox.addWidget(operable_area_W_label)
        operable_area_W_vbox.addWidget(operable_area_W_choice)

        # create operable_area_S vbox
        operable_area_S_vbox = QVBoxLayout()
        operable_area_S_label = QLabel("S Op. Window Area [ft2]")
        operable_area_S_choice = REVIVEDoubleSpinBox(parent=zone_widget)
        operable_area_S_vbox.addWidget(operable_area_S_label)
        operable_area_S_vbox.addWidget(operable_area_S_choice)

        # create operable_area_E vbox
        operable_area_E_vbox = QVBoxLayout()
        operable_area_E_label = QLabel("E Op. Window Area [ft2]")
        operable_area_E_choice = REVIVEDoubleSpinBox(parent=zone_widget)
        operable_area_E_vbox.addWidget(operable_area_E_label)
        operable_area_E_vbox.addWidget(operable_area_E_choice)

        # add to hbox
        zone_hbox.addLayout(zone_name_vbox)
        zone_hbox.addLayout(zone_vbox)
        zone_hbox.addLayout(bedroom_occupancy_vbox)
        zone_hbox.addLayout(chi_vbox)
        zone_hbox.addLayout(operable_area_N_vbox)
        zone_hbox.addLayout(operable_area_W_vbox)
        zone_hbox.addLayout(operable_area_S_vbox)
        zone_hbox.addLayout(operable_area_E_vbox)
        zone_widget.setLayout(zone_hbox)
        return zone_widget
    
    def change_items(self, choices):
        self.choices = choices
        for x in super().__iter__():
            insul_combobox = x.findChildren(REVIVEComboBox)[1]
            insul_combobox.change_items(self.choices)
    
    def __iter__(self):
        for x in super().__iter__():
            comboboxes = x.findChildren(REVIVEComboBox)
            dbspinboxes = x.findChildren(REVIVEDoubleSpinBox)
            interface_widg = comboboxes[0]
            insulation_widg = comboboxes[1]
            perimeter_widg = dbspinboxes[0]
            depth_widg = dbspinboxes[1]
            yield (interface_widg, insulation_widg, perimeter_widg, depth_widg)


class REVIVEFoundationWidgetSet(REVIVEDeletableWidgetSet):
    def __init__(self, add_label="Add", initial_widgets=1, max_widgets=5, label="", is_groupbox=False, parent=None):
        self.choices = []
        super().__init__(add_label, initial_widgets, max_widgets, label, is_groupbox)
    
    def create_widget(self):
        foundation_widget = QWidget()
        foundation_hbox = QHBoxLayout()

        # create interface vbox
        interface_vbox = QVBoxLayout()
        interface_label = QLabel("Interface")
        interface_choice = REVIVEComboBox(items=["Basement", "Crawlspace", "Slab"],
                                          parent=foundation_widget)
        interface_vbox.addWidget(interface_label)
        interface_vbox.addWidget(interface_choice)

        # create insulation vbox
        insulation_vbox = QVBoxLayout()
        insulation_label = QLabel("Insulation")
        insulation_choice = REVIVEComboBox(parent=foundation_widget)
        insulation_choice.change_items(self.choices)
        insulation_vbox.addWidget(insulation_label)
        insulation_vbox.addWidget(insulation_choice)

        # create perimeter vbox
        perimeter_vbox = QVBoxLayout()
        perimeter_label = QLabel("Perimeter (ft)")
        perimeter_choice = REVIVEDoubleSpinBox(parent=foundation_widget)
        perimeter_vbox.addWidget(perimeter_label)
        perimeter_vbox.addWidget(perimeter_choice)

        # create depth vbox
        depth_vbox = QVBoxLayout()
        depth_label = QLabel("Depth (ft)")
        depth_choice = REVIVEDoubleSpinBox(parent=foundation_widget)
        depth_vbox.addWidget(depth_label)
        depth_vbox.addWidget(depth_choice)

        # add to hbox
        foundation_hbox.addLayout(interface_vbox)
        foundation_hbox.addLayout(insulation_vbox)
        foundation_hbox.addLayout(perimeter_vbox)
        foundation_hbox.addLayout(depth_vbox)
        foundation_widget.setLayout(foundation_hbox)
        return foundation_widget
    
    def change_items(self, choices):
        self.choices = choices
        for x in super().__iter__():
            insul_combobox = x.findChildren(REVIVEComboBox)[1]
            insul_combobox.change_items(self.choices)
    
    def __iter__(self):
        for x in super().__iter__():
            comboboxes = x.findChildren(REVIVEComboBox)
            dbspinboxes = x.findChildren(REVIVEDoubleSpinBox)
            interface_widg = comboboxes[0]
            insulation_widg = comboboxes[1]
            perimeter_widg = dbspinboxes[0]
            depth_widg = dbspinboxes[1]
            yield (interface_widg, insulation_widg, perimeter_widg, depth_widg)
        
    

class REVIVESpacer(QWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(10)




def stack_widgets_vertically(widget_list, label_list):
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


def stack_widgets_horizontally(widget_list, label_list):
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