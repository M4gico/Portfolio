from Scripts.LocalServer.Connection import ConnectionClient

class CameraSettingsAPI:

    def __init__(self, connection_interface: ConnectionClient):
        self._connection = connection_interface

    @property
    def exposure(self):
        return self._connection.send_message_return_value("camera.exposure")

    @exposure.setter
    def exposure(self, value: float):
        self._connection.send_message(f"camera_widget.set_exposure({value})")

    @property
    def auto_button(self):
        return self._connection.send_message_return_value("camera_widget.auto_button.isChecked()")

    @auto_button.setter
    def auto_button(self, value: bool):
        if not isinstance(value, bool):
            print(f"Auto button take bool value, not {type(value)}")
            return
        self._connection.send_message(f"camera_widget.set_auto_button({value})")

    @property
    def tec_state(self):
        return self._connection.send_message_return_value("camera_widget.tec_button.isChecked()")

    @tec_state.setter
    def tec_state(self, value: bool):
        self._connection.send_message(f"camera_widget.set_tec({value})")

    @property
    def tec_setpoint(self):
        return self._connection.send_message_return_value("camera_widget.tec_set_point.value()")

    @tec_setpoint.setter
    def tec_setpoint(self, value: int):
        self._connection.send_message(f"camera_widget.tec_set_point.setValue({value})")

    @property
    def fan(self):
        return self._connection.send_message_return_value("camera_widget.fan_button.isChecked()")

    @fan.setter
    def fan(self, value: bool):
        self._connection.send_message(f"camera_widget.set_fan({value})")

    @property
    def frame_averaging(self):
        return self._connection.send_message_return_value("camera_widget.frame_average_button.isChecked()")

    @frame_averaging.setter
    def frame_averaging(self, value: bool):
        self._connection.send_message(f"camera_widget.set_frame_averaging({value})")

    @property
    def max_frame_average(self):
        return self._connection.send_message_return_value("camera_widget.max_frame_average_spinbox.value()")

    @max_frame_average.setter
    def max_frame_average(self, value):
        self._connection.send_message(f"camera_widget.max_frame_average_spinbox.setValue({value})")

    @property
    def frame_rate(self):
        return self._connection.send_message_return_value("camera_widget.actual_frame_average_label.text()")

    # region Gain handler

    @property
    def high_gain(self):
        return self._connection.send_message_return_value("camera_widget.h_gain_button.isChecked()")

    @high_gain.setter
    def high_gain(self, value: bool):
        self._set_high_gain(value)

    @property
    def low_gain(self):
        return self._connection.send_message_return_value("camera_widget.l_gain_button.isChecked()")

    @low_gain.setter
    def low_gain(self, value: bool):
        self._set_high_gain(not value)

    def _set_high_gain(self, value: bool):
        self._connection.send_message(f"camera_widget.set_high_gain({value})")

    # endregion

    # region Settings Handler
    def save_settings(self, setting_type: str):
        """
        Save light or dark settings
        param: "light" or "dark"
        """
        if not (setting_type == "light" or setting_type == "dark"):
            print("ERROR: Wrong setting type put in parameter")
            return
        self._connection.send_message(f"camera_widget.save_settings('{setting_type}')")

    def save_settings_light(self):
        self.save_settings("light")

    def save_settings_dark(self):
        self.save_settings("dark")

    def load_settings(self, setting_type: str):
        """
        Load light or dark settings
        param: "light" or "dark"
        """
        if not (setting_type == "light" or setting_type == "dark"):
            print("ERROR: Wrong setting type put in parameter")
            return
        # Add ' ' around setting_type to give a string parameter to the method
        self._connection.send_message(f"camera_widget.load_settings('{setting_type}')")

    def load_settings_light(self):
        self.load_settings("light")

    def load_settings_dark(self):
        self.load_settings("dark")

    # endregion