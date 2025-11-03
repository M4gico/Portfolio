import sys

from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSettings
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QSpinBox, QRadioButton, \
    QApplication, QMainWindow, QLineEdit, QSlider, QMessageBox

from Scripts.Translation_stage.translation_stage_interface import TranslationStageInterface
from Scripts.Widgets.CustomWidget.QLineEdit import ValueWithUnitInputWidget

from Scripts.Camera.camera_interface import CameraInterface
from Scripts.Camera.raptor_ninox640II import RaptorNinox640II
from Scripts.Widgets.camera_picture_widget import CameraPictureWidget

class TecTempThread(QThread):
    """
    Emit the value of the PCB Temperature & the TEC Temperature every 250 ms
    """
    temp_value_changed = pyqtSignal(str, str)  # signal that send the val of the temperature + tec to cam settings

    def __init__(self, camera):
        super().__init__()
        self.raptor = camera

    def run(self):
        while True:
            tec = "{:.2f}".format(self.raptor.temp)
            temp_pcb = "{:.2f}".format(self.raptor.temp_pcb)
            self.temp_value_changed.emit(tec, temp_pcb)
            self.msleep(250)  # Sleep for 250 milliseconds

class CheckAxisMovingThread(QThread):
    """
    Check if the axis moving
    -> Use for frame averaging
    """
    axis_moving = pyqtSignal()

    def __init__(self, camera_settings):
        super().__init__()
        self.translation_pi = TranslationStageInterface()
        self.camera_settings: CameraSettings = camera_settings
        self.camera_settings.timeValueChanged.connect(self.set_wait_time)
        self.wait_time: int = 500

    def run(self):
        while True:
            if self.translation_pi.is_any_axis_moving():
                self.axis_moving.emit()
            self.msleep(self.wait_time)


    def set_wait_time(self, time: float):
        """
        Wait checking connected to the frame rate of the camera
        """
        self.wait_time = int(time*1000)

#TODO: Mettre un logo check pour save les settings
#TODO: Récupérer la valeur du slider du cameraPicture dans le save setting

class CameraSettings(QWidget):
    """ Display the settings of the camera and allow action on them"""
    timeValueChanged = pyqtSignal(float)  # signal that send the val of the exposure time to the picture thread

    def __init__(self, picture_widget: CameraPictureWidget):
        super().__init__()
        self._raptor = CameraInterface()
        self._picture_widget = picture_widget
        self.saved_dark_settings = {
            "HighGain": None, "LowGain": None, "TecButton": None, "FanButton": None,
            "AutoButton": None, "ExpVal": None, "TecVal": None, "FrameAveraging": None,
            "MaxFrameAverage": None, "DigitalGain": None
        }
        # Settings take in the start of the application
        self.saved_light_settings = {
            "HighGain": None, "LowGain": None, "TecButton": None, "FanButton": None,
            "AutoButton": None, "ExpVal": None, "TecVal": None, "FrameAveraging": None,
            "MaxFrameAverage": None, "DigitalGain": None
        }
        init_settings = {
            "HighGain": False, "LowGain": True, "TecButton": True, "FanButton": True,
            "AutoButton": False, "ExpVal": "0.00125", "TecVal": "-20", "FrameAveraging": False,
            "MaxFrameAverage": 10, "DigitalGain": 256,
        }
        self.auto_exp_val = False
        self.auto = False
        self.time_value = 1
        self.time_unit = 'ms'
        self.max_frame_average = 10
        self.frame_average_counter = 0

        layout = QVBoxLayout()
        layout.addLayout(self.layout_exposure())
        layout.addLayout(self.layout_gain())
        layout.addLayout(self.layout_cooling())
        layout.addLayout(self.layout_frame_rate())
        layout.addLayout(self.layout_frame_average_average())
        layout.addLayout(self.layout_save())
        layout.addLayout(self.layout_load())
        # layout.addLayout(self.layout_debug())

        self.setLayout(layout)
        self.load_light_settings(init_settings)

        # Create thread for temperature
        self.temp_thread = TecTempThread(self._raptor)  # Start the thread who periodically send position values
        self.temp_thread.temp_value_changed.connect(self.update_tec_temp)  # Connect signal-> to function-> display the values
        self.temp_thread.start()

        # Thread to reset frame average if axis moving
        self.check_axis_thread = CheckAxisMovingThread(self)
        self.check_axis_thread.axis_moving.connect(self.reset_frame_average)
        self.check_axis_thread.start()

        self.exposure_changed()

    def update_tec_temp(self, tec, temp_pcb):
        """
        Refresh the screen with new values collected by the thread -> Tec & Temp
        """
        self.actual_tec.setText(tec)
        self.actual_temp_pcb.setText(temp_pcb)

    #region Save settings

    def layout_save(self) -> QHBoxLayout:
        """
        Display of the "Save light & Dark" buttons
        :return: layout -> to add to the main layout
        """
        save_button1 = QPushButton("Save Settings Light")
        save_button1.clicked.connect(lambda: self.save_settings_widget("light"))
        save_button2 = QPushButton("Save Settings Dark")
        save_button2.clicked.connect(lambda: self.save_settings_widget("dark"))
        # Layout for saving
        layout_save = QHBoxLayout()
        layout_save.addWidget(save_button1)
        layout_save.addWidget(save_button2)
        return layout_save

    def layout_load(self) -> QHBoxLayout:
        """
        Display of the "Load light & Dark" buttons
        :return: layout -> to add to the main layout
        """
        load_button1 = QPushButton("Load Light Settings")
        load_button1.clicked.connect(lambda: self.load_settings_widget("light"))
        load_button2 = QPushButton("Load Dark Settings")
        load_button2.clicked.connect(lambda: self.load_settings_widget("dark"))

        # Layout for loading
        layout_load = QHBoxLayout()
        layout_load.addWidget(load_button1)
        layout_load.addWidget(load_button2)
        return layout_load

    def save_settings_widget(self, settings_type: str):
        """
        When user click on the save light/dark button -> save the values to the corresponding dict
        """
        settings = self.save_light_settings()
        if settings_type == "dark":
            self.saved_dark_settings = settings
            self._raptor.logger.debug("save dark settings", self.saved_dark_settings)
        elif settings_type == "light":
            self.saved_light_settings = settings
            self._raptor.logger.debug("save light settings", self.saved_light_settings)

    def load_settings_widget(self, setting_type):
        setting = self.saved_light_settings if setting_type == "light" else self.saved_dark_settings

        # Check if a parameters has not been set
        if any(parameter is None for parameter in setting.values()):
            QMessageBox.warning(self, "Load settings error",
                                "Need to save {0} setting before loading it".format(setting_type))
            return

        self.load_light_settings(setting)

    def load_light_settings(self, setting: dict):
        """
        :param setting: a dictionary with all interesting values of the camera
        """
        self.h_gain_button.setChecked(setting["HighGain"])
        self.l_gain_button.setChecked(setting["LowGain"])
        self.tec_button.setChecked(setting["TecButton"])
        self.tec_button.setText("TEC enabled") if self.tec_button.isChecked() else self.tec_button.setText(
            "TEC disabled")
        self.fan_button.setChecked(setting["FanButton"])
        self.fan_button.setText("Fan enabled") if self.fan_button.isChecked() else self.fan_button.setText(
            "Fan disabled")
        self.auto_button.setChecked(setting["AutoButton"])
        self.tec_set_point.setValue(int(setting["TecVal"]))
        self.line_edit_exposure.setValue(float(setting["ExpVal"]))
        # TODO: Voir pour override le setChecked pour activer le frame averaging en même temps
        self.frame_average_button.setChecked(setting["FrameAveraging"])
        self.max_frame_average_spinbox.setValue(setting["MaxFrameAverage"])
        self.gain_slider.setValue(setting["DigitalGain"])

        self.max_frame_average = setting["MaxFrameAverage"] #TODO: Override pour l'actualiser automatiquement
        self.set_frame_averaging(setting["FrameAveraging"])
        self.exposure_changed()
        # Actualize the value of the tec
        self.tec_setpoint_changed()
        # self.value_digital_gain(setting["DigitalGain"])


    def save_light_settings(self) -> dict:
        """
        :return: dictionary with all interesting values of the camera
        """
        return {"HighGain": self.h_gain_button.isChecked(), "LowGain": self.l_gain_button.isChecked(),
                "TecButton": self.tec_button.isChecked(), "FanButton": self.fan_button.isChecked(),
                "AutoButton": self.auto_button.isChecked(), "TecVal": self.val_tec_setpoint[:-2],
                "ExpVal": self.line_edit_exposure.value(), "FrameAveraging":self.frame_average_button.isChecked(),
                "MaxFrameAverage": self.max_frame_average_spinbox.value(),
                "DigitalGain": self._raptor.digital_gain
        }

    #endregion

    def layout_frame_rate(self) -> QHBoxLayout:
        """
        Layout of the frame rate value
        :return: layout -> to add to the main layout
        """
        title = QLabel("Frame rate: ")
        self.frame_rate_val = QLabel("0.5 Hz")
        layout_frame_rate = QHBoxLayout()
        layout_frame_rate.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align the layout to the left
        layout_frame_rate.addWidget(title)
        layout_frame_rate.addWidget(self.frame_rate_val)
        return layout_frame_rate

    #region Frame averaging

    def layout_frame_average_average(self) -> QHBoxLayout:
        """
        layout to activate the frame rate averaging and set max average value
        :return: layout -> to add to the main layout
        """

        self.frame_average_button = QPushButton("Frame averaging")
        self.frame_average_button.setCheckable(True)
        self.frame_average_button.clicked.connect(self.activate_frame_average)

        label_max_frame = QLabel("Max frame average: ")

        self.max_frame_average_spinbox = QSpinBox()
        self.max_frame_average_spinbox.setMinimum(1)
        self.max_frame_average_spinbox.setMaximum(50)
        self.max_frame_average_spinbox.setValue(10)
        self.max_frame_average_spinbox.setMinimumWidth(30)
        # self.max_frame_average_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        # self.max_frame_average_spinbox.editingFinished.connect(self.set_frame_rate_max_value)
        self.max_frame_average_spinbox.valueChanged.connect(self.set_frame_rate_max_value)

        self.actual_frame_average_label = QLabel()
        self.actualize_frame_average_label()

        layout_frame_average = QHBoxLayout()
        layout_frame_average.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout_frame_average.addWidget(self.frame_average_button)
        layout_frame_average.addWidget(label_max_frame)
        layout_frame_average.addWidget(self.max_frame_average_spinbox)
        layout_frame_average.addWidget(self.actual_frame_average_label)
        return layout_frame_average

    def activate_frame_average(self, checked):
        self._picture_widget.frame_average_check = checked
        self.reset_frame_average()

    def set_frame_rate_max_value(self):
        """
        Set max frame rate for the widget and the camera frame averaging
        """
        value_to_set = self.max_frame_average_spinbox.value()

        self.max_frame_average = value_to_set
        self._picture_widget.max_frame_average = value_to_set

        # Prevent bug that when decrease frame average counter with the spinbox
        if value_to_set < self.frame_average_counter:
            self.frame_average_counter = value_to_set

        self.actualize_frame_average_label()

    def reset_frame_average(self):
        # Reset the frame average counter
        self.frame_average_counter = 0
        # Reset the array stored previously
        self._picture_widget.frame_average_list = None
        # Set the new value to the label
        self.actualize_frame_average_label()

    def actualize_frame_average_label(self):
        self.actual_frame_average_label.setText(f"Frame average: {self.frame_average_counter}/{self.max_frame_average}")

    # Call when a picture is taking during the frame averaging process
    def increment_frame_rate_counter(self):
        if self.frame_average_counter >= self.max_frame_average:
            return
        self.frame_average_counter += 1
        self.actualize_frame_average_label()

    # endregion

    #region Temperature and cooling
    def layout_cooling(self) -> QHBoxLayout:
        """
        Layout of the Fan activation & Tec value
        :return: layout -> to add to the main layout
        """
        actual_tec = "{:.2f}".format(self._raptor.temp)  # value of the real tec value
        actual_temp_pcb = "{:.2f}".format(self._raptor.temp_pcb)  # value of the PCB Temp
        self.tec_set_point = QSpinBox()
        self.tec_set_point.setSuffix("°C")
        self.tec_set_point.setRange(-50, 20)  # Set the range of the spin box -> for temp Cooler
        self.tec_set_point.setSingleStep(1)  # Set the step size of the spin box
        self.tec_set_point.valueChanged.connect(self.tec_setpoint_changed)

        # Creating Widgets
        self.actual_tec = QLabel(actual_tec)
        self.actual_temp_pcb = QLabel(actual_temp_pcb)
        self.tec_button = QPushButton("Enable TEC")
        self.tec_button.setCheckable(True)
        self.tec_button.clicked.connect(self.tec_button_toggled)
        self.fan_button = QPushButton("Enable Fan")
        self.fan_button.setCheckable(True)
        self.fan_button.clicked.connect(self.fan_button_toggled)

        # Creating layout
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align the layout to the left
        layout.addWidget(QLabel("Fan :"))
        layout.addWidget(self.fan_button)
        layout.addWidget(QLabel("TEC Temp :"))
        layout.addWidget(self.actual_tec)
        layout.addWidget(self.tec_button)
        layout.addWidget(QLabel("TEC Setpoint :"))
        layout.addWidget(self.tec_set_point)
        layout.addWidget(QLabel("PCB Temp :"))
        layout.addWidget(self.actual_temp_pcb)
        return layout

    def tec_setpoint_changed(self):
        """
        Update the TEC Setpoint value when the value inside the QSpinbox is changed
        """
        self.val_tec_setpoint = self.tec_set_point.text()
        tec_mode = self._raptor.tec_activation
        if tec_mode == 1:  # if TEC is enabled then -> send the new value
            self._raptor.tec = int(self.val_tec_setpoint[:-2])

    def tec_button_toggled(self, checked: bool):
        """
        Enable or disable the TEC utilisation when the button is toggled
        :param checked: value (True/False) state from the button
        """
        if checked:
            self.tec_button.setText("TEC enabled")
            self._raptor.tec_activation = 1
        else:
            self.tec_button.setText("TEC disabled")
            self._raptor.tec_activation = 0

    def fan_button_toggled(self, checked: bool):
        """
        Enable or disable the Fan utilisation when the button is toggled
        :param checked: value (True/False) state from the button
        """
        if checked:
            self.fan_button.setText("Fan enabled")
            self._raptor.fan = 1
        else:
            self.fan_button.setText("Fan disabled")
            self._raptor.fan = 0

    #endregion

    #region Exposure

    def layout_exposure(self) -> QHBoxLayout:
        """
        Layout of the auto/manual exposure time
        :return: layout -> to add to the main layout
        """
        title = QLabel("Exposure Time :")

        self.line_edit_exposure = ValueWithUnitInputWidget(None, unit='s')
        self.line_edit_exposure.setMinimumWidth(60)
        self.line_edit_exposure.editingFinished.connect(self.exposure_changed)  # When the enter key is pressed

        # Auto button
        self.auto_button = QPushButton("AUTO")
        self.auto_button.setCheckable(True)
        self.auto_button.clicked.connect(self.auto_button_toggled)  # when the button is clicked -> call the function

        layout_Hz = QHBoxLayout()
        layout_Hz.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout_Hz.addWidget(title)
        layout_Hz.addWidget(self.line_edit_exposure)
        layout_Hz.addWidget(self.auto_button)
        return layout_Hz

    def exposure_changed(self):
        """
        Update the exposure time & frame rate when the input is changed + emit signal to change the refresh time of
        the Picture Display
        """

        value = self.line_edit_exposure.value()
        if not self.auto_exp_val and value != 0:  # if not in AUTO mode  -> send the modified values
            value_frame = value
            # Cap the frame to send to the camera to 60 Hz
            if value_frame < 1/30:
                value_frame = 1/30
            self._raptor.logger.debug(f"Time send to the camera: {value_frame} ")

            frame_rate_changed = round(1 / value_frame, 2)
            self.frame_rate_val.setText("{:.2f} Hz".format(frame_rate_changed))  # Display the new text
            self.timeValueChanged.emit(value_frame)  # Send the value for the Picture Display

            exposure_value = round(value*0.9, 9)

            self._raptor.exposure = exposure_value

    def auto_button_toggled(self, checked: bool):
        """
        Auto or Manual mode selection for exposure time and digital gain
        :param checked: value (True/False) of the button
        """
        self.auto_exp_val = checked
        if self.auto_exp_val:
            self.gain_slider.setEnabled(False)
            self._raptor.auto_exposure = 1
            self.frame_rate_val.setText("Auto Exposure Value")  # Change the text of the QLabel
        else:
            self.gain_slider.setEnabled(True)
            self.gain_slider.setValue(0)
            self._raptor.auto_exposure = 0
            self.exposure_changed()

    #endregion

    #TODO: Peut etre faire un bouton pour reset les valeurs au cas où il y a un bug sur la caméra

    #region Gain
    def layout_gain(self) -> QHBoxLayout:
        """
        Layout of the low/high gain choice
        :return: layout -> to add to the main layout
        """
        title_gain = QLabel("Gain :")
        self.h_gain_button = QRadioButton("High Gain")
        self.l_gain_button = QRadioButton("Low Gain")
        self.h_gain_button.toggled.connect(self.gain_button_toggled)
        self.l_gain_button.toggled.connect(self.gain_button_toggled)

        title_digital_gain = QLabel("Digital Gain: ")

        self.gain_slider = QSlider()
        self.gain_slider.setOrientation(Qt.Orientation.Horizontal)
        self.gain_slider.setMaximum(65535)
        self.gain_slider.setMinimum(256)
        self.gain_slider.setValue(256)
        self.value_digital_gain(256)
        self.gain_slider.valueChanged.connect(self.value_digital_gain)

        # Layout for gain choice
        layout_gain = QHBoxLayout()
        layout_gain.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout_gain.addWidget(title_gain)
        layout_gain.addWidget(self.h_gain_button)
        layout_gain.addWidget(self.l_gain_button)
        layout_gain.addWidget(title_digital_gain)
        layout_gain.addWidget(self.gain_slider)
        return layout_gain

    def gain_button_toggled(self):
        """
        Enable or disable the High or Low Gain
        """
        # Get the object that send the signal
        button = self.sender()
        if button.text() == "Low Gain":
            self._raptor.gain = 0
        else:
            self._raptor.gain = 1

    def value_digital_gain(self, value):
        self._raptor.digital_gain = value

    #endregion

    def change_time_unit(self, text):
        self.time_unit = text

    def layout_debug(self):
        """
        Debug layout
        """
        button = QPushButton("Debug digital gain")
        button.clicked.connect(self.refresh_debug_value)

        self.line_exposure = QLineEdit("Digital Gain: ")

        layout = QHBoxLayout()
        layout.addWidget(button)
        layout.addWidget(self.line_exposure)
        return layout

    def refresh_debug_value(self):
        digital_gain_value = self._raptor.digital_gain
        self.line_exposure.setText(f"Digital gain: {int(digital_gain_value)}")

    def save_settings(self) -> dict:
        return {
            "LightSettings": self.saved_light_settings,
            "DarkSettings": self.saved_dark_settings,
        }

    def load_settings(self, setting: dict):
        self.saved_dark_settings = setting["DarkSettings"]
        self.saved_light_settings = setting["LightSettings"]

    # region Method for server/client communication
    def set_exposure(self, value: float):
        self.line_edit_exposure.setValue(value)
        self.exposure_changed()

    def set_auto_button(self, value: bool):
        self.auto_button.setChecked(value)
        self.auto_button_toggled(value)

    def set_high_gain(self, value: bool):
        self.h_gain_button.setChecked(value)
        self.l_gain_button.setChecked(not value)
        self._raptor.gain = value

    def set_fan(self, value: bool):
        self.fan_button.setChecked(value)
        self.fan_button_toggled(value)

    def set_tec(self, value: bool):
        self.tec_button.setChecked(value)
        self.tec_button_toggled(value)

    def set_frame_averaging(self, value: bool):
        self.frame_average_button.setChecked(value)
        self.activate_frame_average(value)

    #endregion

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        camera_picture_widget = CameraPictureWidget()
        camera_widget = CameraSettings(camera_picture_widget)
        self.setCentralWidget(camera_widget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


