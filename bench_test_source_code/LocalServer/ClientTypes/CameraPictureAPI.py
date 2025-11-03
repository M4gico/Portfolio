from Scripts.LocalServer.Connection import ConnectionClient
import math

class CameraPictureAPI:

    def __init__(self, connection_interface: ConnectionClient):
        self._connection = connection_interface

    @property
    def slider_pixel(self):
        """
        return value of the slider in %
        """
        value = int(self._connection.send_message_return_value("camera_picture_widget.slider.value()")) / 163.83
        return math.ceil(value)  # Round the value

    @slider_pixel.setter
    def slider_pixel(self, value: float):
        """
        Set the value of the slider in %
        """
        # Clamp the value between 100 and 0
        if value > 100:
            value = 100
            print("WARNING: value is too high, max is 100")
        elif value < 0:
            value = 0
            print("WARNING: value is too low, min is 0")

        self._connection.send_message(f"camera_picture_widget.slider.setValue({int(value*655.35)})")