from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout

from toolbox3.geometry.point import Point3D

from Scripts.Translation_stage.translation_stage_interface import TranslationStageInterface
from Scripts.Translation_stage.translation_stage_pi import TranslationPi

class GetPosThread(QThread):
    """
    Ask the XYZ Stage the position of the axis.
    """
    position_changed = pyqtSignal(Point3D)

    def __init__(self):
        super().__init__()
        self.translation = TranslationStageInterface()

    def run(self):
        while True:
            pos = self.translation.get_position()
            self.position_changed.emit(pos)
            self.msleep(500)  # Sleep for 500 milliseconds


class GetPosWidget(QWidget):
    """
    Display the position on the interface every X ms using a thread.
    """
    def __init__(self):
        super().__init__()

        self.labels = {"Get Position": QLabel("Get Position"), "X Axis": QLabel("Init"),
                       "Y Axis": QLabel("Init"), "Z Axis": QLabel("Init")}
        self.layout_pos = QHBoxLayout()

        for label in self.labels.values():
            self.layout_pos.addWidget(label)

        self.setLayout(self.layout_pos)
        self.thread = GetPosThread()  # Start the thread who periodically send position values
        self.thread.position_changed.connect(self.update_labels)  # Connect the signal to the function -> display the values
        self.thread.start()
        self.pos: Point3D = Point3D(0, 0, 0)

    @pyqtSlot(Point3D)
    def update_labels(self, pos: Point3D):
        """
        Update the position values collected by the thread
        """
        self.pos = pos
        self.labels["X Axis"].setText(f"X Axis: {pos.x}")
        self.labels["Y Axis"].setText(f"Y Axis: {pos.y}")
        self.labels["Z Axis"].setText(f"Z Axis: {pos.z}")

