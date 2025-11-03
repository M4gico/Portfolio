from PyQt6.QtCore import QEventLoop, QTimer

from Scripts.LocalServer.ClientCommunication import ChatClient

"""
Base class to send message by the client
"""
class ConnectionClient:
    def __init__(self):
        self._client = ChatClient()
        self.time_waiting_response = 0

    def connect_to_server(self, server_name="EMMIServer"):
        self._client.connect_to_server(server_name)
        # Waiting that the server response that the client is right connected -> Avoid bugs
        self._waiting_server_response()

    @property
    def is_connected(self):
        return self._client.is_connected

    def send_message_return_value(self, message) -> str:
        self.send_message(message)

        # Get the response of the server after waiting its response
        if self.response_server == "":
            print(f"ERROR: Error during the reading of the server response: {self.response_server=}")
            return "ERROR"

        if "Return value" in self.response_server:
            return self.response_server.split(":")[1].strip()

    def send_message(self, message):
        if not self.is_connected:
            return "ERROR: Not connected"

        self._client.send_message(message)

        self._waiting_server_response()

    def _waiting_server_response(self):
        # Reset the value of the timeout
        self.time_waiting_response = 0
        loop = QEventLoop()

        check_to_quit_loop = QTimer()
        check_to_quit_loop.timeout.connect(lambda: self._check_response(loop))
        check_to_quit_loop.start(50)  # Check every 50ms if the server has a response
        loop.exec()

        # Stop the check of the response
        check_to_quit_loop.stop()

    def _check_response(self, loop: QEventLoop):
        """
        Wait as long as the server send a response
        :param loop: The loop that will execute this method
        """
        return_bool, response = self._client.is_a_new_message_arrived()
        self.time_waiting_response += 1

        if return_bool:
            self.response_server = response
            loop.quit()

        # If waiting the response more than 3s
        if self.time_waiting_response >= 60:
            print("ERROR: Timeout expired for received response to the client")
            loop.quit()
