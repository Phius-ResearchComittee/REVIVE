# native imports
import json

# dependency imports
from PySide6.QtGui import QCursor
from PySide6.QtCore import (
    Qt,
    Slot
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QPlainTextEdit
)

# custom imports
from gui_utility import *

class HelpTab(QWidget):
    def __init__(self, parent):
        
        # call widget init
        super().__init__()
        self.parent = parent

        # assign external content file handles
        self.help_tree_struc_file = parent.help_tree_struc_file
        self.help_content_file = parent.help_tree_content_file

        # create top-level widgets
        self.layout = QVBoxLayout()
        self.help_page_header = QLabel(f"{self.parent.app_name} v{self.parent.version_no} Help Page", 
                                       alignment=Qt.AlignHCenter)
        self.help_content_layout = QHBoxLayout()

        # add widgets to main layout
        self.layout.addWidget(self.help_page_header)
        self.layout.addLayout(self.help_content_layout)
        
        # build content tree widget
        self.content_tree = REVIVEHelpTree()
        self.top_level_items, self.all_items = self.content_tree.populate_from_file(
            self.help_tree_struc_file
        )

        # build content display widget
        self.content_display = QPlainTextEdit()
        self.content_display.setReadOnly(True)
        self.content_display.cursorPositionChanged.connect(lambda : self.content_display.viewport().setCursor(self.parent.cursor()))
        self.content_display.setFocusPolicy(Qt.NoFocus)

        # enable action to display content when selected
        self.content_tree.itemSelectionChanged.connect(self.display_content)

        # add inner level widgets to horizontal layout
        self.help_content_layout.addWidget(self.content_tree)
        self.help_content_layout.addWidget(self.content_display)

        # resize to maximize text display area
        self.help_content_layout.setStretch(0,0)
        self.help_content_layout.setStretch(1,1)

        # set the layout
        self.setLayout(self.layout)


    @Slot()
    def display_content(self):
        # get current selected topic
        current_topic = self.content_tree.selectedItems()[0]
        key = current_topic.text(0)

        # read content regarding current topic
        with open(self.help_content_file, "r") as json_reader:
            content_dict = json.load(json_reader)
            topic_content = content_dict.get(key, "")
            self.content_display.setPlainText(topic_content)
