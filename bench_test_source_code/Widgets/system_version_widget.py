from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout

from Scripts.Camera.camera_interface import CameraInterface
from Scripts.Camera.raptor_ninox640II import RaptorNinox640II
from Scripts.Translation_stage.translation_stage_interface import TranslationStageInterface
from Scripts.Translation_stage.translation_stage_pi import TranslationPi


class SystemVersion(QWidget):
    """
    Tab 2 : Version of the equipment
    """
    def __init__(self):
        super().__init__()
        self.raptor = CameraInterface()
        self.translation = TranslationStageInterface()
        title_label = QLabel("System Version")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        info = self.raptor.information()
        #First error call man data
        man_data = self.raptor.data_manufacturer
        variables = {
            "Camera Version": "Raptor640II",
            "Camera Serial Number": man_data[0],
            "Camera Build Date": man_data[1],
            "FPGA Version": info[4],
            "Microcontroller Version": info[3],
            "XYZ Stage Serial Number": self.translation.info(),
        }
        layout = QVBoxLayout()  # Create a vertical layout
        layout.addWidget(title_label)  # Add the title label
        layout2 = QGridLayout()
        i = 0
        for variable_name, variable_value in variables.items():  # Add variable labels to the layout
            label_name = QLabel(f"{variable_name}")
            label_val = QLabel(f"{variable_value}")
            layout2.addWidget(label_name, i, 0)
            layout2.addWidget(label_val, i, 1)
            i = i + 1
        layout.addLayout(layout2)
        self.setLayout(layout)