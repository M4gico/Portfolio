from Scripts.LocalServer.Connection import ConnectionClient

class PositionSettingsAPI:

    def __init__(self, connection_interface: ConnectionClient):
        self._connection = connection_interface

    @property
    def speed(self):
        speed = self._connection.send_message_return_value("translation_stage.speed")
        speed = speed.split("=")[1]
        return 5 * float(speed)  # Convert it to a %

    @speed.setter
    def speed(self, value: float):
        self._connection.send_message(f"position_settings_widget.set_speed({value})")

    @property
    def acceleration(self):
        acceleration = self._connection.send_message_return_value("translation_stage.acceleration")
        acceleration = acceleration.split("=")[1]
        return float(acceleration) / 4  # Convert it to a %

    @acceleration.setter
    def acceleration(self, value: float):
        self._connection.send_message(f"position_settings_widget.set_acceleration({value})")

    def init_axis(self):
        self._connection.send_message("position_settings_widget.init_axis_button_toggled()")

    def init_joystick(self):
        self._connection.send_message("position_settings_widget.init_joystick_button_toggled()")

    @property
    def joystick_state(self):
        return self._connection.send_message_return_value("position_settings_widget.joystick_button.isChecked()")

    @joystick_state.setter
    def joystick_state(self, state: bool):
        self._connection.send_message(f"position_settings_widget.set_joystick_state({state})")