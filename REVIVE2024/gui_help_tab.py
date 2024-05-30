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

class HelpTab(QWidget):
    def __init__(self, parent):
        
        # call widget init
        super().__init__()
        self.parent = parent

        # create top-level widgets
        self.layout = QVBoxLayout()
        self.help_page_header = QLabel(f"{self.parent.app_name} v{self.parent.version_no} Help Page", 
                                       alignment=Qt.AlignHCenter)
        self.help_content_layout = QHBoxLayout()

        # add widgets to main layout
        self.layout.addWidget(self.help_page_header)
        self.layout.addLayout(self.help_content_layout)
        
        # build content tree widget
        self.content_tree = QTreeWidget()
        self.content_tree.setColumnCount(1)
        self.content_tree.setHeaderLabels(["Topics"])

        # build content display widget
        self.content_display = QPlainTextEdit()
        self.content_display.setReadOnly(True)
        self.content_display.cursorPositionChanged.connect(lambda : self.content_display.viewport().setCursor(self.parent.cursor()))
        self.content_display.setFocusPolicy(Qt.NoFocus)

        # assign external content file handles
        self.help_tree_struc_file = "help_tree_structure.txt"
        self.help_content_file = "help_tree_content.json"

        # populate content 
        self.populate_content_tree()

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


    def populate_content_tree(self):
        self.top_level_items = []
        self.all_items = [] # items to be tuple of (item, level)
        with open(self.help_tree_struc_file, "r") as reader:
            for line in reader:
                # find the beginning of the word
                level = 0
                while line[level] == "-": level += 1

                # create the tree widget item
                name = line[level:].strip()
                tree_item = QTreeWidgetItem([name])

                # add to list of tree item list
                self.all_items.append((tree_item, level))

                # find parent topic if child topic
                if level > 0:
                    parent_level = level-1

                    # iterate through all items backwards to find most recent
                    for i in range(1,len(self.all_items)+1):
                        curr_item = self.all_items[-i]
                        
                        # check if the current item is the target level
                        if curr_item[1] == parent_level:
                            curr_item[0].addChild(tree_item)
                            break
                
                # if topic has no parent add to top level items
                else:
                    self.top_level_items.append(tree_item)

        # place top level items in tree
        self.content_tree.insertTopLevelItems(0, self.top_level_items)
    

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
