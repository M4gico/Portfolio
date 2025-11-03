import logging
import re
import sys

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLineEdit, QLabel

from Scripts.Camera.camera_interface import CameraInterface
from Scripts.Translation_stage.translation_stage_interface import TranslationStageInterface
from Scripts.Widgets.position_settings_widget import PositionSettings
from Scripts.utils import LoggingClass
from Scripts.Camera.raptor_ninox640II import RaptorNinox640II
from Scripts.Translation_stage.translation_stage_pi import TranslationPi
from Scripts.Widgets.camera_settings_widgets import CameraSettings
from Scripts.Widgets.picture_settings_widget import PictureSettings
from Scripts.Widgets.camera_picture_widget import CameraPictureWidget
from Scripts.Widgets.position_widget import GetPosWidget


class LocalServer(LoggingClass):
    # Add type of parameter for facility to access there class
    def __init__(self, camera_widget: CameraSettings,
                 picture_settings_widget: PictureSettings, camera_picture_widget: CameraPictureWidget,
                 position_widget: GetPosWidget, position_settings_widget: PositionSettings):
        LoggingClass.__init__(self)

        # region Create reference for objects
        self._raptor = CameraInterface()
        self._translation_stage = TranslationStageInterface()
        self._camera_widget = camera_widget
        self._picture_settings_widget = picture_settings_widget
        self._camera_picture_widget = camera_picture_widget
        self._position_widget = position_widget
        self._position_settings_widget = position_settings_widget

        # Object that can be communicated with by the client
        self._object_map = {
            "camera": self._raptor,
            "translation_stage": self._translation_stage,
            "camera_widget": self._camera_widget,
            "picture_settings_widget": self._picture_settings_widget,
            "camera_picture_widget": self._camera_picture_widget,
            "position_settings_widget": self._position_settings_widget
        }

        #endregion

        self.server = QLocalServer()
        self.client = None

        # If a new connection with a client, run handle_new_connection
        self.server.newConnection.connect(self.handle_new_connection)

    def start_server(self, server_name="EMMIServer"):
        # Stop the server if it's already running
        QLocalServer.removeServer(server_name)

        # Start listening if data come from a client
        listen = self.server.listen(server_name)
        if listen:
            self.logger.debug(f"Server start on: {self.server.fullServerName()}")
            return True
        else:
            self.logger.error(f"Error at the start of the server: {self.server.errorString()}")
            return False

    def handle_new_connection(self):
        """
        Automatically called when the server has a new connection
        """
        self.logger.debug("Try new connection with a client")

        # Till the server has a new connection
        while self.server.hasPendingConnections():
            client_socket = self.server.nextPendingConnection()

            # If a client has been connected
            if client_socket:
                self.client = client_socket
                # Call the method if the client send a message to server
                self.client.readyRead.connect(self.handle_client_data)
                self.client.disconnected.connect(self.handle_client_disconnected)
                self.send_message_to_client("Server connected")

                self.logger.debug("Connection with client success")

    def handle_client_data(self):
        """
        Automatically called when the server has a new message from the client
        """
        # Check if the data send by the client is not null
        if self.client.bytesAvailable() == 0:
            self.logger.error("Data send by the client is null")
            return

        data_client = ""
        try:
            data_client = self.client.readAll().data().decode('utf-8')
            # If the data client is null, stop the method
            if not data_client:
                self.logger.error("Error during read the message in the server")
                return

            self.logger.debug(f"Message send by the client to the server: {data_client}")

            # If set a value, exec the message, else eval the message
            if "=" in data_client or self._is_function_execution(data_client):
                value_to_return = exec(data_client, self._object_map)
            else:
                value_to_return = eval(data_client, self._object_map)

            self.logger.debug(f"Return value {data_client}: {value_to_return}")
            self.send_message_to_client(f"Return value : {value_to_return}")

        except Exception as e:
            self.logger.error(f"Error during lecture of client data: {e}, {data_client=}")

    def _is_function_execution(self, text):
        # Check if the string have () with characters in
        return bool(re.search(r"\([^)]*\S[^)]*\)", text))

    def send_message_to_client(self, message):
        # If the client is connected
        if self.client:
            try:
                self.client.write(message.encode('utf-8'))
                # Send all data directly that are stored in the buffer
                self.client.flush()
                self.logger.debug(f"Message send by the server to the client: {message}")
            except Exception as e:
                self.logger.error(f"Error to send message to the client by the server: {e}")

    def handle_client_disconnected(self):
        """
        Automatically called when the client disconnect from the server
        """
        self.client = None
        self.logger.debug("Client disconnected")

    def stop_server(self):
        # Close connection to the client if the server has a connection
        if self.client:
            self.client.close()

        self.server.close()
        self.logger.debug("Close the server")


if __name__ == "__main__":
    pass
    # app = QApplication(sys.argv)
    #
    # # region Debug Handler
    # handlerTerminal = logging.StreamHandler()
    # handlerTerminal.setLevel(logging.DEBUG)
    #
    # formatter = logging.Formatter("%(levelname)s - %(thread)d - %(name)s - %(message)s")
    # handlerTerminal.setFormatter(formatter)
    #
    # localServer.logger.addHandler(handlerTerminal)
    # localServer.logger.setLevel(logging.DEBUG)
    # #endregion
    #
    # # Démarrer le serveur
    # localServer.start_server()
    #
    # # print(f"client of the server: {localServer.client}")
    # # print(f"State client: {local_client.is_connected()}")
    # #
    # # # Utiliser un QTimer pour envoyer le message après que la connexion soit établie
    # # def send_delayed_message(message):
    # #
    # #     if local_client.is_connected():
    # #         local_client.send_message(message)
    # #         print("Message envoyé!")
    # #     else:
    # #         print("Client pas encore connecté, nouvel essai...")
    # #         QTimer.singleShot(100, send_delayed_message)  # Réessayer dans 100ms
    # #
    # # # Envoyer le message après 500ms pour laisser le temps à la connexion
    # # QTimer.singleShot(500, lambda: send_delayed_message("FLAG"))
    # # QTimer.singleShot(500, lambda: send_delayed_message("NEW MESSAGE"))
    # #
    # # # Arrêter l'application après 3 secondes pour les tests
    # # def stop_app():
    # #     local_client.disconnect_from_server()
    # #     localServer.stop_server()
    # #     app.quit()
    # #
    # # QTimer.singleShot(3000, stop_app)
    #
    # # Lancer la boucle d'événements Qt
    # sys.exit(app.exec())
