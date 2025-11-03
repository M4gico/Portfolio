import os.path
import re
import time

from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtWidgets import QInputDialog, QLineEdit, QMessageBox

from Scripts.Translation_stage.translation_stage_interface import TranslationStageInterface


class ToolboxGUI:

    @staticmethod
    def ask_user_text(parent) -> str:
        # Create a dialog to insert the file name
        name_file, check = QInputDialog().getText(parent, "File name", "Insert file name: ", QLineEdit.EchoMode.Normal)

        if not check:
            return "ERROR"

        # Check basic file name (letters, numbers, dashes, underscores)
        valid_pattern = r"^[a-zA-Z0-9_-]+$"

        if not re.match(valid_pattern, name_file):
            QMessageBox.warning(parent, "Name file error", "File name must only inclues (letters, numbers,"
                                                         " dashes and underscores")
            return "ERROR"

        # Check if the user press Ok and insert text
        if not name_file:
            QMessageBox.warning(parent, "Name file error", "Error during input of the file name")
            return "ERROR"

        return name_file

    @staticmethod
    def wait_axis_moving(parent):
        # Reset the value of the timeout
        time_waiting_response = 0
        loop = QEventLoop()

        def _check_axis_moving(parent, loop: QEventLoop, timer):
            """
            Wait as long as the platine stop to move
            :param loop: The loop that will execute this method
            """
            timer += 1
            time.sleep(0.05)

            if not TranslationStageInterface().is_any_axis_moving():
                loop.quit()

            # If waiting more than 10s
            if timer >= 200:
                QMessageBox.warning(parent, "Timeout error", "The calibration had an error, retry")
                loop.quit()

        check_to_quit_loop = QTimer()
        check_to_quit_loop.timeout.connect(lambda: _check_axis_moving(parent, loop, time_waiting_response))
        check_to_quit_loop.start(50)  # Check every 20ms
        loop.exec()

        # Stop the check of the response
        check_to_quit_loop.stop()

    @staticmethod
    def wait_file_is_creating(parent, path_file: str):
        if path_file == "" or path_file is None:
            return

        # Reset the value of the timeout
        time_waiting_response = 0
        loop = QEventLoop()

        def _check_file_is_created(parent, loop: QEventLoop, timer):
            """
            Wait as long as the platine stop to move
            :param loop: The loop that will execute this method
            """
            timer += 1
            time.sleep(0.05)

            # If the file is created
            if os.path.isfile(path_file):
                loop.quit()

            # If waiting more than 10s
            if timer >= 200:
                QMessageBox.warning(parent, "Timeout error", "The calibration had an error, retry")
                loop.quit()

        check_to_quit_loop = QTimer()
        check_to_quit_loop.timeout.connect(lambda: _check_file_is_created(parent, loop, time_waiting_response))
        check_to_quit_loop.start(50)  # Check every 50ms
        loop.exec()

        # Stop the check of the response
        check_to_quit_loop.stop()



