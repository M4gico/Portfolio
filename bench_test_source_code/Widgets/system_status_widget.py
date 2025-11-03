from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout

from Scripts.Camera.camera_interface import CameraInterface
from Scripts.Camera.raptor_ninox640II import RaptorNinox640II


class SystemStatus(QWidget):
    """
    Tab 1 : Display of the status of the equipment
    """

    def __init__(self):
        super().__init__()
        self.raptor = CameraInterface()
        title_label = QLabel("System Status")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        info = self.raptor.information()
        man_data = self.raptor.data_manufacturer
        variables = {
            "FPGA booted successfully": info[0],
            "FPGA not in reset": info[1],
            "Comm to FPGA EPROM": info[2],
            "Bit per Pixel": man_data[6],
            "Picture Dimension": f"{man_data[7]}x {man_data[8]}y",
            "ADC Value": f"{man_data[2]}/{man_data[3]}",
            "DAC Value": f"{man_data[4]}/{man_data[5]}"
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
            i = i+1
        layout.addLayout(layout2)
        self.setLayout(layout)
