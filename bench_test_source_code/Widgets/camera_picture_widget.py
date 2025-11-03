import os.path
import shutil
import sys
import types

import numpy as np

from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot, Qt, QSettings
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSlider, QHBoxLayout, QMainWindow, QApplication, QSizePolicy, \
    QFileDialog, QMessageBox, QDialog, QDialogButtonBox
import pyqtgraph as pg
from typing_extensions import Union

from Scripts.Camera.camera_interface import CameraInterface
from Scripts.Camera.raptor_ninox640II import RaptorNinox640II
from Scripts.ToolboxGUI import ToolboxGUI

#TODO: Regler bug avec l'histogramme qui freeze

class PictureThread(QThread):
    """
    Ask the camera to take a picture and save it in an array, every X sec (=exposure time).
    """
    picture_changed = pyqtSignal()

    def __init__(self, raptor_ninox640II: RaptorNinox640II, frame_sleep):
        super().__init__()
        self.raptor = raptor_ninox640II
        self.frame_sleep = frame_sleep  # in seconds

    def run(self):
        """
        Loop of the thread : take a picture + save it every X sec
        """
        while True:
            self.raptor.capture_img()
            self.picture_changed.emit()
            self.msleep(self.frame_sleep)


class CameraPictureWidget(QWidget):
    """
    Layout that display the new image from the camera every X ms, using a thread.
    """

    frame_average_picture_take = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._raptor = CameraInterface()
        self.frame_sleep = int(100/3)  # 30 Hz by default

        #region camera picture size constraints
        self.img_label = QLabel()
        # Keep the ratio of the camera resolution
        self.img_label.setMinimumSize(320, 256)
        self.img_label.setMaximumSize(960, 768)

        # The widget change its size dynamically vertically and horizontally compared that the window size
        self.img_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Avoid stretching of the widget
        self.img_label.setScaledContents(False)
        #endregion

        self.main_layout()

        self.overlay_image_check = False
        self.overlay_image = None

        self.subtract_image_check = False
        self.subtract_image_list = []

        self.frame_average_list = None
        self.frame_average_check = False
        self.max_frame_average = 10
        self.max_value_pixel = 65535

        # Overlay crosshair
        self.crosshair_visible = False
        self.crosshair_color = Qt.GlobalColor.yellow

        self._thread = None
        self.launch_thread()

    def main_layout(self):
        layout_slider = self.slider_level_layout()
        layout_img = QVBoxLayout()  # Create a layout for PictureProcess
        layout_img.addWidget(self.img_label)
        layout_histogram = self.histogram_layout()

        layout = QHBoxLayout()
        layout.addLayout(layout_img)
        layout.addLayout(layout_slider)
        layout.addLayout(layout_histogram)
        self.setLayout(layout)

    def slider_level_layout(self) -> QVBoxLayout:
        """
        Create a slider to adjust the contrast of the picture
        """
        self.slider = QSlider(Qt.Orientation.Vertical)
        self.slider.setRange(0, 65535)
        self.slider.setValue(65535)
        self.slider.valueChanged.connect(self.change_max_pixel_level)
        layout = QVBoxLayout()
        layout.addWidget(self.slider)
        return layout

    def change_max_pixel_level(self, value):
        self.max_value_pixel = value
        self.frame_average_list = None

    def histogram_layout(self):
        """
        Show the histogram of the value pixel of the picture
        """
        histogram_widget = pg.GraphicsLayoutWidget()
        histogram_widget.setBackground("transparent")
        histogram_widget.setMaximumWidth(100)

        self.hist_lut = pg.HistogramLUTItem()

        # Hide not useful feature
        self.hist_lut.gradient.hide()
        self.hist_lut.region.hide()
        self.hist_lut.axis.hide()

        # Can't change the size of the histogram with the mouse
        self.hist_lut.vb.setMouseEnabled(x=False, y=False)
        self.hist_lut.vb.setDefaultPadding(0)
        self.hist_lut.vb.setContentsMargins(0, 0, 0, 0)

        # Put the curve in white
        self.hist_lut.fillHistogram(color=(0, 0, 0))
        # Put the padding at 0 to avoid max value of 70.000 and take place for nothing
        self.hist_lut.setHistogramRange(0, 65535, 0)

        histogram_widget.addItem(self.hist_lut)

        layout = QVBoxLayout()
        layout.addWidget(histogram_widget)
        return layout


    @pyqtSlot()
    def load_image(self, array_picture: np.ndarray):
        """
        Display the new image that the camera has saved.
        """
        # Set the array to show the histogram
        self.hist_lut.setImageItem(pg.ImageItem(np.stack([array_picture, array_picture])))

        # Change the picture compared to the state of the picture treatment set
        array_picture = self.apply_treatment_picture(array_picture)

        # .mirrored to flip the picture vertical
        # camera_width*8 give bytes per line (lines*uint16*4(RGBA))
        array_img = QImage(array_picture, self._raptor.width, self._raptor.height, self._raptor.width*8,
                           QImage.Format.Format_RGBX64).mirrored(False, True)
        # Crop 2px border to delete black border
        img = QPixmap.fromImage(array_img).copy(2, 2, 638, 510)
        # Scaled the picture compared of the GUI
        smaller_img = img.scaled(self.img_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)

        smaller_img = self.draw_crosshair(smaller_img)

        self.img_label.setPixmap(smaller_img)  # Crop the 2 black pixel border

    #region Picture treatment

    # TODO: A refactor pour que ca soit plus modulaire
    def apply_treatment_picture(self, array_picture: np.ndarray) -> np.ndarray:
        """
        Apply treatment picture depends on set in the GUI
        :param array_picture: image capture by the camera
        :return: image capture with treatment set
        """
        # If the value of a pixel is uppermore than the max_value set, set it to a white pixel
        # Handle the value by the slider in the picture widget
        array_picture[array_picture > self.max_value_pixel] = 65535

        if self.subtract_image_check and self.frame_average_check:
            array_picture = self.frame_average_calculation(array_picture)
            for subtract_picture in self.subtract_image_list:
                # Turn the dtype to int16 to have negative value
                # If keep the dtype to unit16, negative value will return an overflow, so near 65000
                # Can use uint16 because the camera is on 14 data bits
                array_picture = np.subtract(array_picture, subtract_picture, dtype=np.int32)
                # If values are negative, put it at 0
                array_picture = np.clip(array_picture, 0, None)

            # Return in uint16 to avoid bug with overlay mode
            array_picture = array_picture.astype(dtype=np.uint16)
        else:
            if self.subtract_image_check:
                for subtract_picture in self.subtract_image_list:
                    # Turn the dtype to int16 to have negative value
                    # If keep the dtype to unit16, negative value will return an overflow, so near 65000
                    # Can use uint16 because the camera is on 14 data bits
                    array_picture = np.subtract(array_picture, subtract_picture, dtype=np.int32)
                    # If values are negative, put it at 0
                    array_picture = np.clip(array_picture, 0, None)

                # Return in uint16 to avoid bug with overlay mode
                array_picture = array_picture.astype(dtype=np.uint16)

            if self.frame_average_check:
                array_picture = self.frame_average_calculation(array_picture)

        if self.overlay_image_check:
            # Apply in the red and green section of the array the overlay picture pixels
            array_picture = np.stack([array_picture, array_picture, self.overlay_image, array_picture], axis=-1)
        else:
            # Create a 2D array to split R, G, B and A
            # axis = -1 to stack to the last axis
            array_picture = np.stack([array_picture, array_picture, array_picture, array_picture], axis=-1)\
                .astype(np.uint16)

        return array_picture

    def frame_average_calculation(self, array_picture: np.ndarray) -> np.ndarray:
        """
        Make an average of pictures take by the camera depends on the value set in the GUI
        :param array_picture: New picture take by the camera
        :return: The average of all pictures stored depending on the length set in the GUI
        """
        if not array_picture.shape == (640, 512):
            return array_picture

        # Create a 3D array to concatenate with an existing 3D array
        array_picture_3D = np.expand_dims(array_picture, axis=0)

        if self.frame_average_list is None:
            self.frame_average_list = array_picture_3D
            return self.frame_average_list

        # Prevent bug when decrease the value of max_frame_average
        while self.frame_average_list.shape[0] > self.max_frame_average:
            # Delete the last element put in the array
            self.frame_average_list = self.frame_average_list[1:]

        # Add the new array picture to the list
        self.frame_average_list = np.concatenate((self.frame_average_list, array_picture_3D), axis=0)

        # Emit that a picture is taking in the frame averaging system to actualize widget of the camera
        self.frame_average_picture_take.emit()
        # Calculate the average of the array
        # axis = 0 for calculates the mean of each lines
        return np.mean(self.frame_average_list, axis=0).astype(np.uint16)

    def draw_crosshair(self, pixmap: QPixmap) -> QPixmap:
        """
        Draw a crosshair
        :param pixmap: the image of the camera
        :return: the image with the crosshair overlay
        """
        if not self.crosshair_visible:
            return pixmap

        painter = QPainter(pixmap)
        # Create the pen to draw the crosshair
        pen = QPen(self.crosshair_color)
        pen.setWidth(2)
        painter.setPen(pen)

        # Get pixmap dimension
        width = pixmap.width()
        height = pixmap.height()
        # Use // to avoid float number
        center_x = width // 2
        center_y = height // 2

        # Get the maximum size of the crosshair compared to the pixmap to avoid a bigger crosshair
        cross_size = min(width, height) // 20

        # Draw from center_x - cross_size to center_x + cross_size on the y center of the pixmap
        painter.drawLine(center_x - cross_size, center_y, center_x + cross_size, center_y)
        painter.drawLine(center_x, center_y - cross_size, center_x, center_y + cross_size)

        painter.end()
        return pixmap

    #endregion

    def folder_path(self, folder_name) -> str:
        """
        :return: path of the folder compared of the QSettings of the user
        """
        picture_path = QSettings("Serma", "EMMI").value("folderPath")
        return picture_path + "/{}".format(folder_name)

    def save_pixmap_picture_folder(self, file_name: str, folder_name: str) -> Union[QPixmap, None]:
        """
        Save in file explorer the picture show with all picture treatment
        :return: The pixmap saved in the picture folder
        """
        folder_path = self.folder_path(folder_name)
        # Check if the folder Picture exist
        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)

        picture_path = folder_path + "/{}".format(file_name + ".png")

        # Check if the file already exist
        if os.path.isfile(picture_path):
            button = QMessageBox.warning(
                self,
                "Save warning",
                f"{file_name} already exist, do you want to overwrite it ?",
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                defaultButton=QMessageBox.StandardButton.Yes
            )
            if button == QMessageBox.StandardButton.No:
                return None

        ToolboxGUI.wait_axis_moving(self)

        picture = self.img_label.pixmap()
        if picture:
            picture.save(picture_path)

        ToolboxGUI.wait_file_is_creating(self, picture_path)

        return picture

    def remove_folder_files(self, folder_name: str):
        # Get all files in the folder
        folder_path = self.folder_path(folder_name)

        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)

        for entry in os.listdir(folder_path):
            entry_path = os.path.join(folder_path, entry) # Get directory of the file

            if os.path.isfile(entry_path) or os.path.islink(entry_path):
                os.remove(entry_path)
            elif os.path.isdir(entry_path):
                shutil.rmtree(entry_path) # Delete the folder and its content

    def capture_img(self) -> np.ndarray:
        """
        :return: Array show in the GUI
        """
        if self.frame_average_check:
            # Get the frame average show
            picture = np.mean(self.frame_average_list, axis=0).astype(np.uint16)
        else:
            picture = self._raptor.capture_img()

        if picture is None:
            QMessageBox.critical(self, "Save picture error", "Error during capture image of the camera")
            return np.zeros(self._raptor.xdim*self._raptor.ydim).astype(np.uint16)

        return picture

    @pyqtSlot(float)
    def update_time_value(self, time_value: float):
        """
        Change the value of the time sleep when the signal from exposure changed is emitted
        :param time_value: value of the exposure time in seconds from the QlineEdit
        """
        self.frame_sleep = int(time_value * 1000)  # Convert time value to milliseconds
        self.actualize_frame_rate()

    def launch_thread(self):
        """
        Start the thread to display picture
        """
        self._thread = PictureThread(self._raptor, self.frame_sleep)
        # Connect the signal to the function -> display the pic
        self._thread.picture_changed.connect(lambda: self.load_image(self._raptor.last_img))
        self._thread.start()

    def actualize_frame_rate(self):
        """
        When exposure changed, actualize the frame rate of the camera
        """
        self._thread.frame_sleep = self.frame_sleep

class MainWindow(QMainWindow):
    def __init__(self, raptor_camera):
        super().__init__()
        picture_widget = CameraPictureWidget()
        self.setCentralWidget(picture_widget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    cam = CameraInterface()
    window = MainWindow(cam)
    window.show()
    sys.exit(app.exec())
