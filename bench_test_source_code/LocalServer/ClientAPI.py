import math
import sys

from PyQt6.QtWidgets import QApplication

from Scripts.LocalServer.ClientTypes.CameraPictureAPI import CameraPictureAPI
from Scripts.LocalServer.ClientTypes.CameraSettingsAPI import CameraSettingsAPI
from Scripts.LocalServer.ClientTypes.PictureSettingsAPI import PictureSettingsAPI
from Scripts.LocalServer.ClientTypes.PositionSettingsAPI import PositionSettingsAPI
from Scripts.LocalServer.Connection import ConnectionClient


class ClientAPI:

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.connection = ConnectionClient()

        self.camera_settings = CameraSettingsAPI(self.connection)
        self.camera_picture = CameraPictureAPI(self.connection)
        self.picture_settings = PictureSettingsAPI(self.connection)
        self.position_settings = PositionSettingsAPI(self.connection)



if __name__ == '__main__':
    clientAPI = ClientAPI()
    clientAPI.connection.connect_to_server()

    clientAPI.camera_settings.frame_averaging = True