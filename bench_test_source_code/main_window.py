"""
Fenetre principale de l'interface du logiciel du banc EMMI
"""
import sys

from PyQt6.QtCore import QSettings

from Scripts.Camera.camera_interface import CameraInterface
from Scripts.Translation_stage.translation_stage_interface import TranslationStageInterface
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QWidget, \
    QTabWidget, QSizePolicy, QMessageBox, QFileDialog

from Scripts.Widgets.CustomWidget.QFolderDialog import QFolderDialog
from Scripts.Widgets.camera_settings_widgets import CameraSettings
from Scripts.Widgets.camera_picture_widget import CameraPictureWidget
from Scripts.Widgets.grillage_widget import GrillageWidget
from Scripts.Widgets.position_settings_widget import PositionSettings
from Scripts.Widgets.position_widget import GetPosWidget
from Scripts.Widgets.picture_settings_widget import PictureSettings
from Scripts.Widgets.system_settings_widget import SystemSettings

from Scripts.LocalServer.Server import LocalServer
import logging

#TODO: Bouton pour prendre une simple photo de ce qui est affiché sans passer par le grillage

#TODO: Injection de code pour faire du traitement d'image

#TODO: Faire grillage et calibration
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Banc EMMI")
        self.setWindowIcon(QIcon("C:\EMMI_Soft\BancEMMI\Resources\Images\EMMI_Logo.png"))

        self.__raptor = CameraInterface()
        # Creating Widgets
        self.camera_picture_widget = CameraPictureWidget()
        self.camera_settings_widget = CameraSettings(self.camera_picture_widget)
        self.pos_settings_widget = PositionSettings()
        self.system_settings_widget = SystemSettings()
        self.get_pos_widget = GetPosWidget()
        self.picture_settings_widget = PictureSettings(self.camera_picture_widget)
        self.grillage_widget = GrillageWidget(self.get_pos_widget, self.camera_picture_widget, self)

        self.camera_picture_widget.frame_average_picture_take.connect(self.camera_settings_widget.increment_frame_rate_counter)
        self.camera_settings_widget.timeValueChanged.connect(self.camera_picture_widget.update_time_value)

        # Widget that can save and load settings between sessions
        self.widgets_with_settings = (self.camera_settings_widget, self.pos_settings_widget, self.picture_settings_widget)

        # Creating the toolbar
        self.create_toolbar()
        # Creating the main layout
        self.create_main_layout()

        self.local_server = LocalServer(self.camera_settings_widget, self.picture_settings_widget, self.camera_picture_widget,
                                        self.get_pos_widget, self.pos_settings_widget)
        self.local_server.start_server()

    def closeEvent(self, event):
        """
        Override the closeEvent method to stop the Fan, the TEC, the camera and the server before closing the application
        :param event: when closing the main window
        :return: the normal return form the basic function closeEvent
        """
        self.__raptor.fan = False
        self.__raptor.tec_activation = False
        del self.__raptor
        self.local_server.stop_server()
        event.accept()
        return QMainWindow.closeEvent(self, event)

    def create_toolbar(self):
        """
        Create the menu at the top of the Main Window
        """
        change_folder = QAction("Modify project folder", self)
        change_folder.setShortcut("Ctrl+F")
        change_folder.triggered.connect(self.modify_project_folder)

        exit_action = QAction("Quitter", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        save_settings = QAction("Save settings", self)
        save_settings.triggered.connect(self.save_settings)

        load_settings = QAction("Load Settings", self)
        load_settings.setShortcut("Ctrl+L")
        load_settings.triggered.connect(self.load_settings)

        # Create the menu
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        file_menu.addAction(save_settings)
        file_menu.addAction(load_settings)
        file_menu.addAction(exit_action)

        edit_menu =  menu.addMenu("&Edit")
        edit_menu.addAction(change_folder)

    def modify_project_folder(self):
        folder_dialog = QFolderDialog()
        response = folder_dialog.exec()

        if not response:
            QMessageBox.warning(self, "Modify project folder", "Error during modify the path of the project folder")
        folder_dialog.close()

    def save_settings(self):
        """
        Save all settings of widgets
        Not use a ini_path for all instance created in the __init__ because the path can be changed by the user anytime
        """
        file_path = QSettings("Serma", "EMMI").value("folderPath")
        if file_path is None or file_path == "":
            QMessageBox.warning(self, "Save settings error", "File path is not set")
            return
        ini_path: str = file_path + "/settings.ini"
        settings = QSettings(ini_path, QSettings.Format.IniFormat)
        settings.clear()

        # Save all settings of each widget in the tuple
        for widget in self.widgets_with_settings:
            settings.setValue(f"{type(widget).__name__}", widget.save_settings())
        settings.sync() # Be sure that save the .ini settings
        print("Settings of the GUI saved in {}".format(ini_path))


    def load_settings(self):
        """
        Load all settings of the .ini file selected
        """
        ini_path = QFileDialog.getOpenFileName(
            self,
            "Open File",
            QSettings("Serma", "EMMI").value("folderPath"),
            "*.ini"
        )[0]
        if ini_path is None or ini_path == "":
            return

        settings = QSettings(ini_path, QSettings.Format.IniFormat)

        if settings is None:
            QMessageBox.warning(self, "Save settings error", "Error during open the .ini file")
            return

        for widget in self.widgets_with_settings:
            widget.load_settings(settings.value(f"{type(widget).__name__}"))

    # region Main layout
    #TODO: A refactor car c'est dur à relire et à rajouter des éléments
    def create_main_layout(self):
        """
        Set the Main Layout by putting all the widgets, from the parameters, together.
        """
        # Avoid bug when not in full-screen
        self.setMinimumSize(800, 600)
        # Keep the resize intelligently
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Preferred
        )

        # Create the main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        main_layout.addLayout(self.left_layout())

        separator_vertical = QFrame()
        separator_vertical.setFrameShape(QFrame.Shape.HLine)
        separator_vertical.setFrameShadow(QFrame.Shadow.Sunken)
        separator_vertical.setLineWidth(2)

        # Create the right layout
        right_layout = QVBoxLayout()
        title_label = QLabel("Camera Settings")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(title_label)
        right_layout.addWidget(self.camera_settings_widget)

        separator_right = QFrame()
        separator_right.setFrameShape(QFrame.Shape.HLine)
        separator_right.setFrameShadow(QFrame.Shadow.Sunken)
        separator_right.setLineWidth(2)
        right_layout.addWidget(separator_right)

        # Picture settings widget
        title_picture_settings = QLabel("Picture Settings")
        title_picture_settings.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(title_picture_settings)
        right_layout.addWidget(self.picture_settings_widget)

        # Add space above the separator
        space_widget = QWidget()
        space_widget.setMinimumHeight(550)  # Adjust the height value to control the spacing
        right_layout.addWidget(space_widget)
        right_layout.addWidget(separator_vertical)
        right_layout.addWidget(self.system_settings_widget)

        vertical_separator = QFrame()
        vertical_separator.setFrameShape(QFrame.Shape.VLine)
        vertical_separator.setFrameShadow(QFrame.Shadow.Sunken)
        vertical_separator.setLineWidth(2)
        main_layout.addWidget(vertical_separator)

        # If need a second tab for a feature
        right_part = QTabWidget()
        camera_settings = QWidget()
        camera_settings.setLayout(right_layout)

        grillage_layout = QVBoxLayout()
        set_point_label = QLabel("Set crosshair")
        set_point_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        # set_grillage_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        grillage_layout.setSpacing(5)
        grillage_layout.addWidget(set_point_label)
        grillage_layout.addWidget(self.grillage_widget)

        grillage_layout.addStretch()

        grillage_widget = QWidget()
        grillage_widget.setLayout(grillage_layout)

        right_part.addTab(camera_settings, "Camera settings")
        right_part.addTab(grillage_widget, "Grillage settings")

        # Create the central widget
        left_part = QWidget()
        left_part.setLayout(main_layout)

        central_layout = QHBoxLayout()
        central_layout.addWidget(left_part, 1)
        central_layout.addWidget(right_part, 1)

        main_principal_layout = QWidget()
        main_principal_layout.setLayout(central_layout)

        self.setCentralWidget(main_principal_layout)

    def left_layout(self) -> QVBoxLayout:
        """
        Left layout creation of the main layout
        """
        # Create the left layout
        left_layout = QVBoxLayout()
        title_camera_label = QLabel("Camera Picture")
        title_camera_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setLineWidth(2)

        title_position_label = QLabel("Position Settings")
        title_position_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        left_layout.addWidget(title_camera_label)
        left_layout.addWidget(self.camera_picture_widget)
        left_layout.addWidget(separator)
        left_layout.addWidget(title_position_label)
        left_layout.addWidget(self.get_pos_widget)
        left_layout.addWidget(self.pos_settings_widget)

        return left_layout

    def right_layout(self):
        pass

    def right_tab(self):
        pass


    # endregion

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pi = TranslationStageInterface(port="COM4", baudrate=115200)

    pi.is_axis_init = True

    cam = CameraInterface()

    # region Debug logger
    # A rajouter le mois et l'année dans le nom du fichier
    # handlerFile = logging.FileHandler(r"Debug\{:%d - %H-%M-%S}.log".format(datetime.now())) #Print the date in the file
    # handlerFile.setLevel(logging.DEBUG)

    handlerTerminal = logging.StreamHandler()
    handlerTerminal.setLevel(logging.WARNING)

    formatter = logging.Formatter("%(levelname)s - %(thread)d - %(name)s - %(message)s")
    # handlerFile.setFormatter(formatter)
    handlerTerminal.setFormatter(formatter)

    # pi.logger.addHandler(handlerFile)
    pi.logger.addHandler(handlerTerminal)
    pi.logger.setLevel(logging.DEBUG)
    # cam.logger.addHandler(handlerFile)
    cam.logger.addHandler(handlerTerminal)
    cam.logger.setLevel(logging.DEBUG)
    # endregion

    window = MainWindow()
    window.showMaximized()  # Show the window maximized
    sys.exit(app.exec())
