from PyQt6.QtWidgets import QWidget, QTabWidget, QVBoxLayout

from Scripts.Camera.raptor_ninox640II import RaptorNinox640II
from Scripts.Translation_stage.translation_stage_pi import TranslationPi
from Scripts.Widgets.system_status_widget import SystemStatus
from Scripts.Widgets.system_version_widget import SystemVersion


class SystemSettings(QWidget):
    """
    Layout of the 2 tabs : information corner
    """
    def __init__(self):
        super().__init__()
        self.tab_widget = QTabWidget()
        system_status = SystemStatus()
        system_version = SystemVersion()
        self.tab_widget.addTab(system_status, "System Status")
        self.tab_widget.addTab(system_version, "System Version")
        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)