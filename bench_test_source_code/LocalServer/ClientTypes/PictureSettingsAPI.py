from Scripts.LocalServer.Connection import ConnectionClient


class PictureSettingsAPI:

    def __init__(self, connection_interface: ConnectionClient):
        self._connection = connection_interface

    def save_static_image(self):
        self._connection.send_message("picture_settings_widget.save_overlay_picture()")

    def save_dark_image(self):
        self._connection.send_message("picture_settings_widget.save_dark_picture()")

    def show_overlay(self, value: bool):
        """
        Show or not the overlay on the picture
        """
        self._connection.send_message(f"picture_settings_widget.show_overlay({value})")

    def subtract_pictures(self, value: bool):
        self._connection.send_message(f"picture_settings_widget.subtract_pictures({value})")