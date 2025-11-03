import importlib.util
import inspect
import sys
import types
from dataclasses import dataclass
from typing import List

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QApplication, QMainWindow, QMessageBox, \
    QStyle, QFileDialog

from Scripts.Camera.camera_interface import CameraInterface
from Scripts.ScriptInjectionExample.GoodTreatment import treatment_black
from Scripts.ToolboxGUI import ToolboxGUI
from Scripts.Widgets.CustomWidget.QCheckableComboBox import QCheckableComboBox, ImageTreatment
from Scripts.Widgets.camera_picture_widget import CameraPictureWidget
from Scripts.Camera.raptor_ninox640II import RaptorNinox640II
from Scripts.Widgets.grillage_widget import GrillageWidget

#TODO: Permettre de soustraire autant d'images qu'on veut
#TODO: Put the layout into a grid layout
class PictureSettings(QWidget):
    def __init__(self, camera_picture_widget: CameraPictureWidget):
        super().__init__()
        self.raptor = CameraInterface()
        self.camera_picture_widget = camera_picture_widget

        os_style = self.style()
        self.check_icon = os_style.standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        self.cancel_icon = os_style.standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)

        camera_picture_btn = QPushButton("Save camera picture")
        camera_picture_btn.setMinimumWidth(350)
        camera_picture_btn.clicked.connect(self.save_camera_picture)

        layout = QVBoxLayout()
        layout.addWidget(camera_picture_btn)
        layout.addLayout(self.layout_overlay_treatment())
        layout.addLayout(self.layout_subtract_treatment())
        layout.addLayout(self.dynamic_picture_treatment_layout())

        self.setLayout(layout)

    def layout_overlay_treatment(self) -> QHBoxLayout:
        self.save_static_image_button = QPushButton("Save static image")
        # self.save_static_image_button.setMinimumWidth(250)

        self.save_static_image_button.setIcon(QIcon(self.cancel_icon))

        self.save_static_image_button.clicked.connect(self.save_overlay_picture)

        self.show_overlay_button = QPushButton("Show overlay")
        # self.show_overlay_button.setMinimumWidth(250)
        self.show_overlay_button.setCheckable(True)
        self.show_overlay_button.clicked.connect(self.show_overlay)

        layout_save_picture = QHBoxLayout()
        # layout_save_picture.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout_save_picture.addWidget(self.save_static_image_button)
        layout_save_picture.addWidget(self.show_overlay_button)

        return layout_save_picture

    def layout_subtract_treatment(self) -> QHBoxLayout:
        self.show_subtract_picture_button = QPushButton("Subtract pictures")
        # self.show_subtract_picture_button.setMinimumWidth(250)
        self.show_subtract_picture_button.setCheckable(True)
        self.show_subtract_picture_button.clicked.connect(self.subtract_pictures)

        self.save_dark_image_button = QPushButton("Add dark image")
        # self.save_dark_image_button.setMinimumWidth(250)
        self.save_dark_image_button.setIcon(QIcon(self.cancel_icon))
        self.save_dark_image_button.clicked.connect(self.save_dark_picture)

        remove_last_image = QPushButton("Remove last image")
        remove_last_image.clicked.connect(lambda: self.camera_picture_widget.subtract_image_list.pop())

        layout = QHBoxLayout()
        # layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.save_dark_image_button)
        layout.addWidget(self.show_subtract_picture_button)
        layout.addWidget(remove_last_image)

        return layout

    def remove_last_dark_image(self):
        self.camera_picture_widget.subtract_image_list.pop()

    def subtract_pictures(self, checked: bool):
        # If the subtract image is not set
        if any(image is None for image in self.camera_picture_widget.subtract_image_list) :
            self.show_subtract_picture_button.setChecked(False)
            QMessageBox.warning(self, "Picture error", "Subtract picture is not set !")
            return

        self.camera_picture_widget.subtract_image_check = checked

    def show_overlay(self, checked: bool):
        # If the overlay image is not set
        if self.camera_picture_widget.overlay_image is None:
            self.show_overlay_button.setChecked(False)
            QMessageBox.warning(self, "Picture error", "Overlay picture is not set !")
            return

        self.camera_picture_widget.overlay_image_check = checked

    def save_overlay_picture(self):
        self.camera_picture_widget.overlay_image = self.camera_picture_widget.capture_img()
        self.save_static_image_button.setIcon(QIcon(self.check_icon))

    def save_dark_picture(self):
        # treatment_name = ToolboxGUI.ask_user_text(self)
        self.camera_picture_widget.subtract_image_list.append(self.camera_picture_widget.capture_img())
        self.save_dark_image_button.setIcon(QIcon(self.check_icon))

    def save_camera_picture(self):
        name_picture = ToolboxGUI.ask_user_text(self)
        self.camera_picture_widget.save_pixmap_picture_folder(name_picture, "Picture")

    #region dynamic script import
    def dynamic_picture_treatment_layout(self) -> QVBoxLayout:
        main_layout = QVBoxLayout()

        choose_treatment_layout = QHBoxLayout()
        # choose_treatment_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        choose_script = QPushButton("Import picture treatment")
        choose_script.clicked.connect(self.add_treatment_items)
        choose_script.setMinimumWidth(250)

        self.toggle_select_items = QCheckableComboBox()
        self.toggle_select_items.setMinimumWidth(250)

        choose_treatment_layout.addWidget(choose_script)
        choose_treatment_layout.addWidget(self.toggle_select_items)

        main_layout.addLayout(choose_treatment_layout)
        return main_layout

    def add_treatment_items(self):
        file_path = QFileDialog.getOpenFileName(
            self,
            "Python script",
            "",
            "*.py"
        )[0]

        # If the user cancel the dialog
        if file_path == "":
            return

        image_treatments = self.get_treatment_from_module(file_path)

        if len(image_treatments) == 0:
            return

        self.toggle_select_items.add_items_from_dict(image_treatments)

    def get_treatment_from_module(self, module_path: str) -> dict[str, types.FunctionType]:
        """
        Get all the function write in a .py file
        :param module_path: .py file path
        :return: List of all image treatment in the .py file
        """
        name = inspect.getmodulename(module_path)
        # Get the module in the name store in the file of the file_path
        spec = importlib.util.spec_from_file_location(name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # Need to execute the module to load its content in the module variable

        image_treatments: dict[str, types.FunctionType] = {}
        # Get all methods in the module
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj):
                # Get parameters and return types of the function
                signature =  inspect.signature(obj)

                if len(signature.parameters) != 1:
                    QMessageBox.warning(self, "Import module error",
                                        "The image treatment function need to have only one parameter")
                    return {}

                func: types.FunctionType = getattr(module, name)
                image_treatments[name] = func

        return image_treatments

    #endregion
    def load_settings(self, setting: dict):
        """
        Load picture treatment
        :param setting: the dictionary for this class
        """
        subtract_image = setting["SubtractImage"]
        self.camera_picture_widget.subtract_image_list = subtract_image
        if subtract_image is not None:
            self.save_dark_image_button.setIcon(QIcon(self.check_icon))

        overlay_image = setting["OverlayImage"]
        self.camera_picture_widget.overlay_image = overlay_image
        if overlay_image is not None:
            self.save_static_image_button.setIcon(QIcon(self.check_icon))

    def save_settings(self) -> dict:
        """
        Save image for picture treatment
        """
        return {
            "SubtractImage": self.camera_picture_widget.subtract_image_list,
            "OverlayImage": self.camera_picture_widget.overlay_image,
        }

class MainWindow(QMainWindow):
    def __init__(self, raptor_camera):
        super().__init__()
        picture_widget = CameraPictureWidget()
        picture_settings = PictureSettings(picture_widget)
        self.setCentralWidget(picture_settings)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    cam = CameraInterface()
    window = MainWindow(cam)
    window.show()
    sys.exit(app.exec())