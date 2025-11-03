import logging
import sys

from PyQt6.QtWidgets import QApplication

from Scripts.Camera.camera_interface import CameraInterface
from Scripts.Translation_stage.translation_stage_interface import TranslationStageInterface
from Scripts.Widgets.CustomWidget.QFolderDialog import QFolderDialog
from Scripts.main_window import MainWindow


def main():
    """
    Launch the application
    """
    app = QApplication(sys.argv)

    print("Application started")

    folder_dialog = QFolderDialog()
    response = folder_dialog.exec()
    if response == folder_dialog.DialogCode.Accepted:
        folder_dialog.close()
    elif response == folder_dialog.DialogCode.Rejected:
        app.quit()
        return
    else:
        raise ValueError(f"Got an unexpected return value from connection dialog: {response}")

    pi = TranslationStageInterface(port="COM4", baudrate=115200)
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

    main_window = MainWindow()
    main_window.showMaximized()
    sys.exit(app.exec())



if __name__ == "__main__":
    main()