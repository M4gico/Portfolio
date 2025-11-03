import sys

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator, QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QComboBox, QLineEdit, QMessageBox, \
    QMainWindow, QApplication, QLabel, QDoubleSpinBox, QAbstractSpinBox
from toolbox3.geometry.point import Point3D

from Scripts.Translation_stage.translation_stage_interface import TranslationStageInterface
from Scripts.Translation_stage.translation_stage_pi import TranslationPi

class PositionSettings(QWidget):
    """
    Display the XYZ Stage's relative actions.
    """

    def __init__(self):
        super().__init__()
        self.translation = TranslationStageInterface()
        self.translation.joystick(0)
        self.move_abs_state = True
        self.inputs = {1: '0', 2: '0', 3: '0'}  # default values
        self.correct_val = [1, 1, 1, 1]
        self.pos_settings = {"X": 0, "Y": 0, "Z": 0,
                             "MoveMode": self.move_abs_state}
        self._speed = 100
        self._acceleration = 100

        # Position Settings's layout
        layout = QVBoxLayout()
        layout.addLayout(self.layout_speed_axis())
        layout.addLayout(self.layout_init())
        layout.addLayout(self.layout_do_move())
        layout.addLayout(self.layout_save_load())
        layout.addLayout(self.layout_enable_joystick())
        self.setLayout(layout)

    def layout_init(self) -> QHBoxLayout:
        """
        Layout of the buttons Init Axis & Init Joystick.
        :return: layout to add to the main layout.
        """
        self.init_axis_button = QPushButton("Initalisation Axis")
        self.init_axis_button.clicked.connect(self.init_axis_button_toggled)
        self.init_joystick_button = QPushButton("Initialisation Joystick")
        self.init_joystick_button.clicked.connect(self.init_joystick_button_toggled)
        # layout move
        layout_init = QHBoxLayout()
        layout_init.addWidget(self.init_axis_button)
        layout_init.addWidget(self.init_joystick_button)
        return layout_init

    def init_axis_button_toggled(self):
        self.translation.init_axis()
        self.joystick_button_toggled(False) # Desactivate joystick when init axis
        self.joystick_button.setChecked(False)
        self.init_axis_button.setText("Init Axis OK")

    def init_joystick_button_toggled(self):
        self.translation.init_joystick()
        self.init_joystick_button.setText("Init Joystick OK")

    def layout_do_move(self):
        """
        Layout of the moving setting's buttons.
        :return: layout -> to add to the main layout.
        """
        self.select_move = QComboBox()  # Choice of Relative or Absolut
        self.select_move.addItems(["Move Absolute", "Move Relative"])
        self.select_move.currentTextChanged.connect(self.select_move_changed)  # Connect signal to the handler method
        # Get pos min & max :
        self.pos_min = self.translation.get_limit_min(1)
        self.pos_max = self.translation.get_limit_max(1)


        # region Input X Y Z
        regex = QRegularExpression(r'^-?\d*\.?\d+$')
        validator = QRegularExpressionValidator(regex)
        self.input_x = QLineEdit()
        self.input_x.setPlaceholderText("0.0 -> 52.0 mm")
        self.input_x.setValidator(validator)
        self.input_y = QLineEdit()
        self.input_y.setPlaceholderText("0.0 -> 52.0 mm")
        self.input_y.setValidator(validator)
        self.input_z = QLineEdit()
        self.input_z.setPlaceholderText("0.0 -> 52.0 mm")
        self.input_z.setValidator(validator)
        self.input_x.textChanged.connect(lambda text, axis=1: self.move_val_changed(text, axis))
        self.input_y.textChanged.connect(lambda text, axis=2: self.move_val_changed(text, axis))
        self.input_z.textChanged.connect(lambda text, axis=3: self.move_val_changed(text, axis))
        # Place after the connection signal to call automatically the method at the start
        self.input_x.setText("0")
        self.input_y.setText("0")
        self.input_z.setText("0")

        #endregion

        move_button = QPushButton("MOVE")  # Move button
        move_button.clicked.connect(self.move_button_clicked)
        layout_move = QHBoxLayout()  # Creating the layout
        layout_move.addWidget(self.select_move)
        layout_move.addWidget(self.input_x)
        layout_move.addWidget(self.input_y)
        layout_move.addWidget(self.input_z)
        layout_move.addWidget(move_button)
        return layout_move

    def layout_save_load(self) -> QHBoxLayout:
        """
        Display the save/load buttons for the position.
        :return: layout -> to add to the main layout.
        """
        self.save_button_pos = QPushButton("Save Position")
        self.save_button_pos.clicked.connect(self.save_pos_settings)
        self.load_button_pos = QPushButton("Load Position")
        self.load_button_pos.clicked.connect(self.load_pos_settings)
        layout = QHBoxLayout()
        layout.addWidget(self.save_button_pos)
        layout.addWidget(self.load_button_pos)
        return layout

    def save_pos_settings(self):
        """
        Saving position in a dictionary & displaying it inside the loading button.
        """
        pos = self.translation.get_position()
        self.pos_settings = {"X": pos.x, "Y": pos.y, "Z": pos.z, "MoveMode": self.move_abs_state}
        self.load_button_pos.setText(
            "Load Position  -  Latest saved position  {}x | {}y | {}z".format(self.pos_settings["X"],
                                                                              self.pos_settings["Y"],
                                                                              self.pos_settings["Z"]))

    def load_pos_settings(self):
        """
        Loading & Moving the axis to the last saved position.
        """
        self.select_move.setCurrentIndex(self.pos_settings["MoveMode"])
        self.input_x.setText(str(self.pos_settings["X"]))
        self.input_y.setText(str(self.pos_settings["Y"]))
        self.input_z.setText(str(self.pos_settings["Z"]))
        self.move_button_clicked()

    def select_move_changed(self, text: str):
        """
        Save the chosen movement : Absolut/Relative.
        """
        if text == "Move Absolute":
            self.move_abs_state = True
        if text == "Move Relative":
            self.move_abs_state = False

    def move_val_changed(self, text, axis):
        """
        :param text: Text from the input.
        :param axis: X Y or Z
        """
        # Prevent error conversion when QlineEdit is empty
        if text == "" or text == "-":
            return
        self.move_value = text
        self.axis = axis
        self.inputs[axis] = self.move_value if self.move_value else 0  # if no inputs then replace the empty field by 0
        # Change background color based on the value of "move_value"
        self.labels = {1: self.input_x, 2: self.input_y, 3: self.input_z}
        self.label = self.labels.get(axis)
        self.background_color()

    def background_color(self):
        """
        Change the background of the line text depends on if the value exceed min or max value
        """
        color = QColor(0, 0, 0)
        min_value = self.pos_min

        # if move relative -> then limited from -52 to 52 and not 0 to 52
        if not self.move_abs_state:
            min_value = -self.pos_max

        try:
            move_value = float(self.move_value)
        except:
            QMessageBox.critical(self, "Background color error", "Error during float conversion of the move value")
            return

        if min_value <= move_value <= self.pos_max:
            color = QColor(240, 255, 243)  # green color
            self.correct_val[self.axis] = 1
        else:
            color = QColor(249, 238, 227)  # red color
            self.correct_val[self.axis] = 0

        self.label.setStyleSheet(f"background-color: {color.name()};")

    def move_button_clicked(self):
        """
        Move to coordinates according to move type
        """
        if self.joystick_button.isChecked() or self.translation.joystick_activation:
            QMessageBox.warning(self, "Move Error",
                                "Moving with coordinates is impossible as long as the joystick is activated")
            return

        if not self.translation.is_axis_init:
            QMessageBox.warning(self, "Move Error", "Moving is impossible as long as the axis are not initialised")
            return

        if self.correct_val[1] & self.correct_val[2] & self.correct_val[3] != 1:
            QMessageBox.warning(self, "Move Error",
                                "Coordinates aren't correct: position available is from 0 to 52mm")
            return

        position = Point3D(float(self.inputs[1]), float(self.inputs[2]), float(self.inputs[3]))

        if self.move_abs_state:
            self.translation.move_absolute(position)
        else:
            check = self.translation.move_relative(position)
            if not check:
                QMessageBox.warning(self, "Move relative error", "You try to move out of the translation stage limit")
                return

    def layout_enable_joystick(self) -> QHBoxLayout:
        """
        Display the button to enable the joystick.
        :return : layout -> widget layout
        """
        # on/off joystick button
        self.joystick_button = QPushButton("Joystick disabled")
        self.joystick_button.setCheckable(True)
        self.joystick_button.clicked.connect(self.joystick_button_toggled)
        # layout move
        layout_joystick = QHBoxLayout()
        layout_joystick.addWidget(self.joystick_button)
        return layout_joystick

    def joystick_button_toggled(self, checked):
        """
        Change the display depending on the activation of the joystick & Activate or not the joystick.
        """

        if checked:
            if not self.translation.is_joystick_init:
                QMessageBox.warning(self, "Joystick activation error", "Joystick is not initialize")
                self.joystick_button.setChecked(False)
                return

            if self.translation.is_any_axis_moving():
                QMessageBox.warning(self, "Joystick activation error", "Can't use joystick during axis moving")
                self.joystick_button.setChecked(False)
                return

            self.joystick_button.setText("Joystick enabled")
            self.translation.joystick(1)
        else:
            self.joystick_button.setText("Joystick disabled")
            self.translation.joystick(0)

    def layout_speed_axis(self) -> QHBoxLayout:
        """
        Control the velocity and the acceleration of axis
        :return : layout -> widget layout
        """
        speed_label = QLabel("Speed:")

        # 0 < Value < 10
        self.speed_spin_box = QDoubleSpinBox()
        self.speed_spin_box.setSuffix("%")
        self.speed_spin_box.setRange(0, 100)
        self.speed_spin_box.setValue(100)
        self.speed_spin_box.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.speed_spin_box.editingFinished.connect(self._modify_speed)  # When the enter key is pressed

        layout_speed = QHBoxLayout()
        layout_speed.addStretch()
        layout_speed.addWidget(speed_label)
        layout_speed.addWidget(self.speed_spin_box)
        layout_speed.addStretch()

        acceleration_label = QLabel("Acceleration:")

        # 0 < Value < 400
        self.accleration_spin_box = QDoubleSpinBox()
        self.accleration_spin_box.setSuffix("%")
        self.accleration_spin_box.setRange(0, 100)
        self.accleration_spin_box.setValue(100)
        self.accleration_spin_box.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.accleration_spin_box.editingFinished.connect(self._modify_acceleration)  # When the enter key is pressed

        # Add stretch to center layout
        layout_acceleration = QHBoxLayout()
        layout_acceleration.addStretch()
        layout_acceleration.addWidget(acceleration_label)
        layout_acceleration.addWidget(self.accleration_spin_box)
        layout_acceleration.addStretch()

        # layout move
        layout_speed_axis = QHBoxLayout()
        layout_speed_axis.addLayout(layout_speed)
        layout_speed_axis.addLayout(layout_acceleration)

        return layout_speed_axis

    def _modify_acceleration(self):
        """
        Max value : 400
        Find max with SEP? command to the address 0x4A = 0d74
        """
        self._acceleration = self.accleration_spin_box.value()
        self.translation.acceleration = (self._acceleration * 400) / 100 #Put % into translation value

    def _modify_speed(self):
        """
        Max value : 20
        Find max with SEP? command to the address 0x49 = 0d73
        Max value send is 10 but can put to 20
        """
        self._speed = self.speed_spin_box.value()
        self.translation.speed = (self._speed * 20) / 100 #Put % into translation value

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, value):
        self._speed = value
        self.speed_spin_box.setValue(value)

    @property
    def acceleration(self):
        return self._acceleration

    @acceleration.setter
    def acceleration(self, value):
        self._acceleration = value
        self.accleration_spin_box.setValue(value)

    def load_settings(self, param: dict):
        self.speed = param["Speed"]
        self.acceleration = param["Acceleration"]

        pos_value = param["SavePos"]
        self.pos_settings["X"] = pos_value["X"]
        self.pos_settings["Y"] = pos_value["Y"]
        self.pos_settings["Z"] = pos_value["Z"]

        # Place the text in axis QLineEdits
        self.input_x.setText(str(pos_value["X"]))
        self.input_y.setText(str(pos_value["Y"]))
        self.input_z.setText(str(pos_value["Z"]))


    def save_settings(self) -> dict:
        return {
            "Speed": self.speed,
            "Acceleration": self.acceleration,
            "SavePos": self.pos_settings
        }

    # region Server method call
    def set_speed(self, value: float):
        self.speed_spin_box.setValue(value)
        self._modify_speed()

    def set_acceleration(self, value: float):
        self.accleration_spin_box.setValue(value)
        self._modify_acceleration()

    def set_joystick_state(self, state: bool):
        self.joystick_button.setChecked(state)
        self.joystick_button_toggled(state)

    # endregion



class MainWindow(QMainWindow):
    def __init__(self, translation_stage):
        super().__init__()
        position_settings = PositionSettings()
        self.setCentralWidget(position_settings)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pi = TranslationStageInterface(port="COM4", baudrate=115200)
    window = MainWindow(pi)
    window.show()
    sys.exit(app.exec())
