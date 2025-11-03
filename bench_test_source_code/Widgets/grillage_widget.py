import os
import re
import sys
import time
from typing import List, Union

import numpy as np
from dataclasses import dataclass
from PIL import Image

from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer, QEventLoop, QDir, QSettings
from PyQt6.QtGui import QIcon, QImage, QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QSpinBox, QRadioButton, \
    QApplication, QMainWindow, QLineEdit, QSlider, QComboBox, QMessageBox, QStyle, QFileDialog, QInputDialog
from toolbox3.geometry.point import Point3D, Point2D

from Scripts.Camera.camera_interface import CameraInterface
from Scripts.ToolboxGUI import ToolboxGUI
from Scripts.Translation_stage.translation_stage_interface import TranslationStageInterface

from Scripts.Widgets.camera_picture_widget import CameraPictureWidget
from Scripts.Widgets.position_widget import GetPosWidget

"""
camera resolution for pos value with 2.5x zoom:
X: 3.8 = 640px
Y: 2.95 = 512px
"""


# CHIP POS : 16, 28, 28.8

@dataclass
class PlanValues:
    """
    Class to store all the values needed to move on the plan after the calibration with landmarks
    """
    x_max: float
    x_min: float
    delta_x: float

    y_max: float
    y_min: float
    delta_y: float

    # Pass it in Point3D when take the z parameter for calibration
    p0: Point2D
    p1: Point2D
    p2: Point2D
    p3: Point2D


class ChipMappingThread(QThread):
    """
    Put the capture of thread to be better visually and see what the camera see
    Otherwise, the camera doesn't show anything if the method is call in the main thread
    """
    # Define signals for communication with main thread
    show_warning = pyqtSignal(str, str)  # title, message
    finished_successfully = pyqtSignal()
    request_user_input = pyqtSignal()  # Signal to request user input from main thread

    def __init__(self, grillage_widget):
        super().__init__()
        self.grillage_widget = grillage_widget
        self.user_input_result = None

    def run(self):
        self.grillage_widget.start_mapping_chip_thread()

    def get_user_input(self) -> str:
        """
        Thread-safe method to get user input from the main thread
        """
        self.user_input_result = None
        self.request_user_input.emit()
        return self.user_input_result if self.user_input_result is not None else "ERROR"


# TODO: Gérer le QMessageBox avec un QThread
# TODO: Faire en fonction du grossissement de l'objectif

class GrillageWidget(QWidget):

    def __init__(self, position_widget: GetPosWidget, camera_picture_widget: CameraPictureWidget,
                 main_window: QMainWindow):
        super().__init__()
        self._camera_picture_widget = camera_picture_widget
        self._position_widget = position_widget
        self._translation_stage = TranslationStageInterface()
        self._raptor = CameraInterface()
        self._main_window = main_window

        self.color_map = {
            "White": Qt.GlobalColor.white,
            "Black": Qt.GlobalColor.black,
            "Red": Qt.GlobalColor.red,
            "Blue": Qt.GlobalColor.blue,
            "Green": Qt.GlobalColor.green,
        }

        self.landmark_position = {
            "O": [None, None],
            "I": [None, None],
            "J": [None, None],
        }
        self.plan_values = PlanValues(0, 0, 0, 0, 0, 0, None, None, None, None)

        self.is_calibrated = False
        self.time_waiting_response = 0

        # Initial value for 2.5x zoom, so not const
        self.x_camera_length: float = 3.9
        self.y_camera_length: float = 3.1

        # Répétition dans picture_settings_widget -> Peut etre trouver une méthode pour éviter cela
        os_style = self.style()
        self.check_icon = os_style.standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        self.cancel_icon = os_style.standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)

        # Create the thread that will be run to take the chip picture
        self.take_chip_picture_thread = ChipMappingThread(self)

        # Connect signals to handle GUI operations from thread
        self.take_chip_picture_thread.show_warning.connect(self.show_warning_message_thread)
        self.take_chip_picture_thread.finished_successfully.connect(self.chip_picture_finished)
        self.take_chip_picture_thread.request_user_input.connect(self.handle_user_input_request_thread,
                                                                 Qt.ConnectionType.BlockingQueuedConnection)

        self.main_layout()

    @property
    def _pos(self):
        return self._position_widget.pos

    def main_layout(self):
        layout = QVBoxLayout()

        layout.addLayout(self.set_zoom_lens_layout())
        layout.addLayout(self.show_crosshair_layout())
        layout.addLayout(self.change_color_crosshair_layout())
        layout.addLayout(self.image_border_set_layout())
        layout.addLayout(self.layout_chip_picture())

        # DEBUG
        btn_debug = QPushButton("DEBUG")
        btn_debug.clicked.connect(lambda: self.save_big_picture_array(self.take_treat_camera_array()))
        layout.addWidget(btn_debug)

        self.setLayout(layout)

    # region crosshair method
    def show_crosshair_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        self.toggle_crosshair_btn = QPushButton("Toggle Crosshair")
        self.toggle_crosshair_btn.setCheckable(True)
        self.toggle_crosshair_btn.clicked.connect(self.toggle_crosshair)

        layout.addWidget(self.toggle_crosshair_btn)

        return layout

    def change_color_crosshair_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        color_label = QLabel("Crosshair color: ")
        color_combo_box = QComboBox()
        color_combo_box.addItems(["White", "Black", "Red", "Blue", "Green"])
        color_combo_box.currentTextChanged.connect(self.change_color_crosshair)
        self.change_color_crosshair("White")  # Weird

        layout.addWidget(color_label)
        layout.addWidget(color_combo_box)

        return layout

    def toggle_crosshair(self, checked):
        self._camera_picture_widget.crosshair_visible = checked

    def change_color_crosshair(self, color_name: str):
        # If no color valid, return the color white
        self._camera_picture_widget.crosshair_color = self.color_map.get(color_name, Qt.GlobalColor.white)

    # endregion

    # region image border setter

    def image_border_set_layout(self) -> QHBoxLayout:
        """
        Layout to set 3 landmark for border the image capture and an image to show where put the landmark
        """
        layout_pos = QVBoxLayout()
        layout_pos.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Creates the 3 landmark pos
        for landmark in ["O", "I", "J"]:
            layout_pos.addLayout(self.capture_axis_pos_layout(landmark))

        self.calibration_btn = QPushButton("Calibrate")
        self.calibration_btn.setIcon(QIcon(self.cancel_icon))
        self.calibration_btn.clicked.connect(self.calibrate_button)

        layout_pos.addWidget(self.calibration_btn)

        layout_image_border = QHBoxLayout()

        chip_border_image = self.chip_diagram_label()

        layout_image_border.addLayout(layout_pos)
        # layout_image_border.addWidget(chip_border_image)

        return layout_image_border

    def capture_axis_pos_layout(self, landmark: str) -> QHBoxLayout:
        """
        Create a button to set the pos of the landmark and show it in a QLabel associated
        """
        layout = QHBoxLayout()

        button_capture = QPushButton()
        button_capture.setText(f'Capture {landmark} landmark')
        label_capture = QLabel(f"Landmark {landmark} position: ")

        # Connect button and label together
        def set_label_pos():
            if not self._translation_stage.is_axis_init:
                QMessageBox.warning(self, "Set Landmark Error", "Axis need to be init to get landmark position")
                return

            if self._translation_stage.is_any_axis_moving():
                QMessageBox.warning(self, "Set Landmark Error", "Can't get the position during axis moving")
                return

            pos = self._pos
            label_capture.setText(
                "Landmark {0} position: {1:.2f}, {2:.2f}, {3:.2f}".format(landmark, pos.x, pos.y, pos.z))
            self.landmark_position[str(landmark)] = pos

        button_capture.clicked.connect(set_label_pos)

        layout.addWidget(button_capture)
        layout.addWidget(label_capture)

        return layout

    def calibrate_button(self):
        """
        Check if the 3 landmark are set
        Call when the calibration button is pressed
        """
        # Check if any values in all array of the dictionary is None
        if any(None in array for array in self.landmark_position.values()):
            QMessageBox.warning(self, "Calibration error", "3 landmarks are not set")
            return

        self.is_calibrated = True
        self.calibration_btn.setIcon(QIcon(self.check_icon))

        # Hide the crosshair on the GUI image
        self.toggle_crosshair_btn.setChecked(False)
        self.toggle_crosshair(False)
        self._calculate_plan_values()

        # Can take a picture
        self.save_file_button.setEnabled(True)

    # noinspection PyTypeChecker
    def _calculate_plan_values(self):
        """
        y_max------------        p0-----------p1
        |               |        |             |
        |               |   ->   |             |
        |               |        |             |
        x_max--------x_min       p2-----------p3
        y_min
        """
        xo_pos = self.landmark_position.get("O")[0]
        yo_pos = self.landmark_position.get("O")[1]

        xi_pos = self.landmark_position.get("I")[0]
        yi_pos = self.landmark_position.get("I")[1]

        xj_pos = self.landmark_position.get("J")[0]
        yj_pos = self.landmark_position.get("J")[1]

        # Add 0.2 to avoid cropping the picture
        x_max = max(xo_pos, xi_pos, xj_pos) + 0.2
        x_min = min(xo_pos, xi_pos, xj_pos) + 0.2

        y_max = max(yo_pos, yi_pos, yj_pos) + 0.2
        y_min = min(yo_pos, yi_pos, yj_pos) + 0.2

        delta_x = x_max - x_min
        delta_y = y_max - y_min

        # Calculate corner pos of the plan
        p0 = Point2D(x_max, y_max)
        p1 = Point2D(x_min, y_max)
        p2 = Point2D(x_max, y_min)
        p3 = Point2D(x_min, y_min)

        self.plan_values = PlanValues(x_max, x_min, delta_x, y_max, y_min, delta_y, p0, p1, p2, p3)

    def chip_diagram_label(self) -> QLabel:
        """
        Create a QLabel to print a diagram of the chip and the position of the 3 landmark
        """
        html_diagram = """
        <div style="font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.2;">
        <span style="color: blue; font-weight: bold;">J</span><span style="color: black;">-----------------</span><br>
        <span style="color: black;">|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|</span><br>
        <span style="color: black;">|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|</span><br>
        <span style="color: black;">|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;CHIP&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|</span><br>
        <span style="color: black;">|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|</span><br>
        <span style="color: black;">|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|</span><br>
        <span style="color: red; font-weight: bold;">O</span><span style="color: black;">-----------------</span><span style="color: green; font-weight: bold;">I</span>
        </div>
        """

        label = QLabel(html_diagram)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    # endregion

    # region chip picture

    def layout_chip_picture(self):
        self.save_file_button = QPushButton("Save grillage picture")
        self.save_file_button.setEnabled(False)
        self.save_file_button.clicked.connect(self.start_chip_picture_thread)

        layout = QHBoxLayout()
        layout.addWidget(self.save_file_button)
        return layout

    #region thread_manager
    def start_chip_picture_thread(self):
        """
        Start the chip picture process in a thread and disable the button to launch it
        """
        if not self.take_chip_picture_thread.isRunning():
            self.save_file_button.setEnabled(False)
            self._main_window.setEnabled(False)
            self.take_chip_picture_thread.start()
        else:
            QMessageBox.warning(
                self,
                "Chip mapping",
                "A chip mapping is already running"
            )

    def show_warning_message_thread(self, title: str, message: str):
        """Use to be called from the pyqt signal in a thread execution"""
        QMessageBox.warning(self, title, message)
        self.save_file_button.setEnabled(True)
        self._main_window.setEnabled(True)

    def handle_user_input_request_thread(self):
        """
        Handle user input request from thread using BlockingQueuedConnection
        This ensures the thread waits for this method to complete
        """
        result = ToolboxGUI.ask_user_text(self)
        self.take_chip_picture_thread.user_input_result = result

    def chip_picture_finished(self):
        self.save_file_button.setEnabled(True)
        self._main_window.setEnabled(True)
        # TODO: Dire que le fichier a été crée et si l'utilisateur veut l'ouvrir

    # noinspection PyTypeChecker
    def start_mapping_chip_thread(self):
        """
        First method call from the thread to make the
        Save the picture of the chip depend on the calibration

        """
        if not self.is_calibrated:
            self.take_chip_picture_thread.show_warning.emit("Calibration error", "The calibration had an error, retry")
            return

        if self._translation_stage.joystick_activation:
            self.take_chip_picture_thread.show_warning.emit("Joystick error",
                                                            "Can't take picture as long as the joystick is activated")
            return

        self._perform_chip_mapping_capture()

        # Emit from the thread that the chip has been captured to stop the thread -> turn on the main window and save picture
        self.take_chip_picture_thread.finished_successfully.emit()

    #endregion

    # region chip_mapping
    def _perform_chip_mapping_capture(self):
        """Do the chip mapping compared of the plan values of the calibration give by the user"""
        delta_x = self.plan_values.delta_x
        delta_y = self.plan_values.delta_y

        # Get numbers of step needed to take all the chip
        step_move_x = int(delta_x // self.x_camera_length) + 1 # Give how many camera length are in delta
        step_move_y = int(delta_y // self.y_camera_length) + 1

        # Remove all files in PictureDraft folder
        self._camera_picture_widget.remove_folder_files("PictureDraft")

        # Crée un array sur toutes l'axe x pour avoir sa longueur
        # Crée un array indépendant sur chaque axe y pour ensuite le concaténer aux autres axe y
        if step_move_x and step_move_y:
            self._capture_xy_grid(step_move_x, step_move_y)

        elif step_move_x:
            self._capture_horizontal_grid(step_move_x, delta_y)

        elif step_move_y:
            self._capture_vertical_grid(step_move_y, delta_x)
        else:
            self._capture_single_picture(delta_x, delta_y)

    def _capture_xy_grid(self, step_move_x, step_move_y):
        big_picture_array = None
        # Start at the middle of the left corner
        start_pos_x = self.plan_values.x_max - self.x_camera_length / 2
        start_pos_y = self.plan_values.y_max - self.y_camera_length / 2

        picture_number = 0

        png_picture_list = []

        print("Start move ts")

        for i in range(step_move_y):
            for j in range(step_move_x):
                picture_number += 1

                pos_x = start_pos_x - j * self.x_camera_length
                pos_y = start_pos_y - i * self.y_camera_length

                self._translation_stage.move_absolute(Point3D(pos_x, pos_y, self._pos.z))

                picture = self._camera_picture_widget.save_pixmap_picture_folder(
                    f"PictureDraft_{picture_number}", "PictureDraft")

                if picture is None:
                    QMessageBox.critical(
                        self,
                        "Save picture draft",
                        f"There is an error during the# saving of the picture draft of 'PictureDraft_{picture_number}'"
                    )

                png_picture_list.append(picture)

        print("Finish move ts")

        big_picture_array = self._concatenate_png_picture(png_picture_list, step_move_x, step_move_y)

        if big_picture_array is None:
            print("ERROR: Failed to concatenate PNG files")
            return

        self.save_big_picture_array(big_picture_array)

    def _capture_horizontal_grid(self, step_move_x, delta_y):
        start_pos_x = self.plan_values.x_max - self.x_camera_length / 2
        # Go to center on y-axis
        start_pos_y = self.plan_values.y_min + delta_y / 2

        for i in range(step_move_x + 1):
            self._translation_stage.move_absolute(
                Point3D(start_pos_x - i * self.x_camera_length, start_pos_y, self._pos.z))

            self._camera_picture_widget.save_pixmap_picture_folder(
                f"Picture_x_{i}", "PictureDraft")

    def _capture_vertical_grid(self, step_move_y, delta_x):
        # Go to center on x-axis
        start_pos_x = self.plan_values.x_min + delta_x / 2
        start_pos_y = self.plan_values.y_max - self.y_camera_length / 2

        for i in range(step_move_y + 1):
            self._translation_stage.move_absolute(
                Point3D(start_pos_x, start_pos_y - i * self.y_camera_length, self._pos.z))

            self._camera_picture_widget.save_pixmap_picture_folder(
                f"Picture_y_{i}", "PictureDraft")

    def _capture_single_picture(self, delta_x, delta_y):
        # Go to center of the grillage
        start_pos_x = self.plan_values.x_min + delta_x / 2
        start_pos_y = self.plan_values.y_min + delta_y / 2

        self._translation_stage.move_absolute(
            Point3D(start_pos_x, start_pos_y, self._pos.z))

        self._camera_picture_widget.save_pixmap_picture_folder(
            f"Picture_single", "PictureDraft")
    # endregion

    def _concatenate_png_picture(self, png_list: List[QPixmap], cols: int, rows: int) -> Union[np.ndarray, None]:
        """
        Concatenate all the png in a list to create a big picture
        :param png_list: The list of the png to concatenate
        :param cols: Number of columns take
        :param rows: Number of rows take
        """
        print("Start to concatenate")
        try:
            if len(png_list) != cols*rows:
                QMessageBox.critical(
                    self,
                    "Concatenate PNG pictures error",
                    "Error in the size of the list compared of the rows and the columns"
                )
                return None

            images_list: List[np.ndarray] = []
            for png in png_list:
                image = png.toImage().convertToFormat(QImage.Format.Format_RGBX64)

                # Get raw bytes from the image
                ptr = image.constBits()
                ptr.setsize(image.sizeInBytes())

                arr = np.frombuffer(ptr, dtype=np.uint16).reshape(image.height(), image.width(), 4)
                images_list.append(arr)

            # Check if all files have the same shape
            reference_shape = images_list[0].shape
            for i, img in enumerate(images_list):
                if img.shape != reference_shape:
                    print(f"ERROR : Image {i} has a different shape: {img.shape} vs {reference_shape}")
                    return None

            # Concatenation of all pictures
            print("Start assembling picture")

            big_picture_array = None
            img_index = 0

            for row in range(rows):
                # Create a new reference
                temp_array = images_list[img_index].copy()
                img_index += 1

                for col in range(1, cols):
                    next_image = images_list[img_index]
                    img_index += 1

                    #Concatenate horizontally (axis=1) the arrays
                    temp_array = np.concatenate((temp_array, next_image), axis=1)

                # At the end of concatenate a new line
                if big_picture_array is None:
                    big_picture_array = temp_array
                else:
                    #Concatenate vertically (axis=0) the arrays
                    big_picture_array = np.concatenate((big_picture_array, temp_array), axis=0)

            print("Finish assembling picture")

            return big_picture_array


        except Exception as e:
            print(f"Error during concatenation of png picture: {e}")
            return None



    def _convert_pixmap_to_array(self, pixmap: QPixmap):
        image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBX64)

        # Get raw bytes from the image
        ptr = image.constBits()
        ptr.setsize(image.sizeInBytes())

        arr = np.frombuffer(ptr, dtype=np.uint16).reshape(image.height(), image.width(), 4)

        return arr


    def take_treat_camera_array(self) -> np.ndarray:
        return self._camera_picture_widget.apply_treatment_picture(self._raptor.capture_img())

    def save_big_picture_array(self, big_array: np.ndarray):
        """
        Save the big array into a path give by the user
        """
        try:
            if not self._check_big_array(big_array):
                return

            big_array_8bit = (big_array / 65535.0 * 255.0).astype(np.uint8)

            img = Image.fromarray(big_array_8bit, mode='RGBA')

            name_file = self.take_chip_picture_thread.get_user_input()

            picture_path = self.picture_folder_path(name_file)

            if picture_path == "":
                return

            if img:
                img.save(picture_path)
                img.show()
        except Exception as e:
            print(f"Save big picture array error : {e}")

    def _check_big_array(self, big_array) -> bool:
        """Check if the big array respect some specifications"""
        if big_array is None:
            self.take_chip_picture_thread.show_warning.emit("Save Error", "No image data to save")
            return False

        shape = big_array.shape

        # Verify the shape, the dimension - should be divisible by camera resolution
        if len(shape) != 3 or shape[2] != 4 or not (shape[0] % 640 == 0 and shape[1] % 512 == 0):
            self.take_chip_picture_thread.show_warning.emit("Big chip picture",
                                                            f"Error: Array shape {shape} is not a valid image format")
            return False

        return True

    # endregion

    def picture_folder_path(self, name_file: str) -> str:
        """
        :return: the path for the file in the picture folder
        """
        if name_file == "ERROR" or name_file == "" or name_file is None:
            return ""
        # Saving in the directory
        picture_path = QSettings("Serma", "EMMI").value("folderPath")
        if picture_path is None or picture_path == "":
            QMessageBox.warning(self, "Save settings error", "File path is not set")
            return ""
        folder_path = picture_path + "/{}".format("Picture")
        # Check if the folder Picture exist
        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)

        return folder_path + "/{}".format(name_file + ".png")

    # region zoom lens
    # TODO: Demander obligatoirement à l'utilisateur l'objectif qu'il utilise
    # TODO: Si un seul landmark est set, ne pas pouvoir calibrer
    def set_zoom_lens_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        lens_label = QLabel("Zoom lens: ")

        lens_dropdown = QComboBox()
        lens_dropdown.addItems(["2.5", "20", "50"])
        lens_dropdown.currentTextChanged.connect(self.set_zoom_lens)

        layout.addWidget(lens_label)
        layout.addWidget(lens_dropdown)
        return layout

    def set_zoom_lens(self, value: str):
        """
        Change the length that the camera see compared that the zoom lens uses
        :param value: value return by the dropdown selection
        """
        match value:
            case "2.5":
                self.x_camera_length = 3.9
                self.y_camera_length = 3.1
            case "20":
                self.x_camera_length = 0.5
                self.y_camera_length = 0.4
            case "50":
                self.x_camera_length = 0.2
                self.y_camera_length = 0.17
            case _:
                QMessageBox.critical(self, "Error set zoom lens", "The zoom lens selected is wrong")
                return

    # endregion

    def load_settings(self):
        pass

    def save_settings(self):
        pass


class MainWindowTest(QMainWindow):
    def __init__(self, raptor_camera, pi):
        super().__init__()
        picture_widget = CameraPictureWidget()
        position_widget = GetPosWidget()
        grillage_widget = GrillageWidget(position_widget, picture_widget, self)
        self.setCentralWidget(grillage_widget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pi = TranslationStageInterface(port="COM4", baudrate=115200)
    cam = CameraInterface()
    pi.is_axis_init = True
    pi.joystick_activation = True
    window = MainWindowTest(cam, pi)
    window.show()  # Show the window maximized
    sys.exit(app.exec())