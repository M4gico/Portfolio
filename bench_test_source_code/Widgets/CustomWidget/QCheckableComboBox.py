import sys
import types
from typing import List, Optional, NamedTuple, Dict

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QPushButton, QMenu, QMainWindow, QApplication, QMessageBox, QHBoxLayout, QWidget


class ImageTreatment(NamedTuple):
    """
    Connect the QAction and the image treatment
    """
    name: str
    img_treatment: types.FunctionType
    action: QAction

class QCheckableComboBox(QPushButton):
    def __init__(self, treatments: dict[str, types.FunctionType] = None):
        super().__init__("Select treatments...")
        self._items: dict[str, ImageTreatment] = {}
        self._selected_items: dict[str, ImageTreatment] = {}

        # Create a menu in the button
        self._menu = QMenu(self)
        self.setMenu(self._menu)

        self._select_all_action = QAction("Select all")
        self._select_all_action.triggered.connect(self.select_all_items)
        self._unselect_all_action = QAction("Unselect all")
        self._unselect_all_action.triggered.connect(self.unselected_all_items)

        self._menu.addAction(self._select_all_action)
        self._menu.addAction(self._unselect_all_action)

        if treatments is not None:
            self.add_items_from_dict(treatments)

    def add_item(self, name: str, func: types.FunctionType):
        """
        Add a picture treatment to items and create a QAction connected
        """
        # Check if the function already exist
        if any(key == name for key in self._items.keys()):
            QMessageBox.warning(self, "Add picture treatment", "This picture treatment already exist")
            return

        # Create the QAction
        action = QAction(name, self)
        action.setCheckable(True)

        # Create a new image treatment connected with its QAction
        img_treatment = ImageTreatment(name, func, action)
        # If its QAction is toggled, add or delete it in the selected items
        img_treatment.action.triggered.connect(lambda checked, item_obj=img_treatment: self.toggle_item(checked, item_obj))

        # Add the image treatment to the items dictionary
        self._items[img_treatment.name] = img_treatment

        # Insert the action just before the unselect button
        self._menu.insertAction(self._unselect_all_action, img_treatment.action)

    def add_items_from_dict(self, dictionary: dict[str,types.FunctionType]):
        """
        Add item from a dictionary of picture treatment
        """
        for name, img_treatment in dictionary.items():
            self.add_item(name, img_treatment)

    def remove_item(self, item: ImageTreatment):
        """
        Remove the item from the items dictionary and selected items
        """

        # If the item is not in items
        if not any(key == item.name for key in self._items.keys()):
            QMessageBox.critical(self, "Remove picture treatment error", "Trying to remove item that doesn't exist")
            return

        self._menu.removeAction(item.action)
        del self._items[item.name]

        # If the item is in selected items
        if any(key == item.name for key in self._selected_items.keys()):
            del self._selected_items[item.action.text()]

    def remove_all_items(self):
        for item in self._items.values():
            self.remove_item(item)

    def select_all_items(self):
        """
        Select all items store in items
        """
        for item in self._items.values():
            # For all items in the items, check if they are not in selected items
            if item not in self._selected_items.values():
                item.action.setChecked(True)
                self._selected_items[item.name] = item
        self.update_text()

    def unselected_all_items(self):
        for item in self._items.values():
            # For all items in the items, check if they are in selected items
            if item in self._selected_items.values():
                item.action.setChecked(False)
                del self._selected_items[item.name]
        self.update_text()

    def toggle_item(self, checked, item: ImageTreatment):
        """
        Handle the item in the selected items dictionary depends of the check send
        """
        if checked:
            self._selected_items[item.name] = item
        else:
            del self._selected_items[item.name]
        self.update_text()

    def update_text(self):
        if self._selected_items:
            self.setText(f"{len(self._selected_items)} selected")
        else:
            self.setText("Select treatments...")

    @property
    def items(self):
        return self._items

    @property
    def selected_items(self):
        return self._selected_items

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())