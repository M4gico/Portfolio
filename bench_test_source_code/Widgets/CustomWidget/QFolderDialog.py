from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QFormLayout, QSpinBox, QVBoxLayout, QDialogButtonBox, QLabel, QPushButton, \
    QFileDialog
from threading import Thread, Lock

class Singleton(type):
    """
    Thread-safe implementation of singleton
    """
    _instances = {}
    # Synchronise threads during access of singleton
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            # Check if an instance of the class doesn't already exist in a singleton
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class QFolderDialog(QDialog):

    def __init__(self):
        super().__init__()
        self._folder_path: str = None

        self.setMinimumSize(250, 125)

        self.setWindowTitle("Saving folder directory")
        self.setWindowIcon(QIcon("/Resources/Images/EMMI_Logo.png"))

        layout = QVBoxLayout()

        save_file_button = QPushButton("Select folder")
        save_file_button.clicked.connect(self.save_folder)

        self.folder_path_label = QLabel("Folder path: ")
        self.folder_path_label.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        # Get the reference of the Ok button
        self.button_ok = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.button_ok.setText("Launch")
        self.button_ok.setEnabled(False)

        layout.addWidget(save_file_button)
        layout.addWidget(self.folder_path_label)
        layout.addWidget(buttons, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

    def save_folder(self):
        """Ouvre une boîte de dialogue pour sélectionner un dossier"""
        self._folder_path = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner un Dossier",
            "C:\EMMI_Soft\BancEMMI",  # Répertoire de départ (vide = répertoire courant)
            QFileDialog.Option.ShowDirsOnly
        )

        if self._folder_path:
            self.button_ok.setEnabled(True)
            self.folder_path_label.setText("Folder path: {}".format(self._folder_path))

            # Store in the QSettings the folder path to get it in other QWidget of the GUI
            # To get values of the same QSettings, give the same constructor parameter
            # Use OS registery to save and access data
            settings = QSettings("Serma", "EMMI")
            settings.setValue("folderPath", self.folder_path)
            del settings

    @property
    def folder_path(self):
        return self._folder_path
