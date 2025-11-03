import logging
import sys

from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtNetwork import QLocalSocket

from Scripts.utils import LoggingClass


class SendMessageThread(QThread):
    """
    Make a timeout for send message and received the confirmation of the server to send a new message
    Avoid to send 2 messages too fast and the server can't interpret it
    """
    def __init__(self, chat_client):
        super().__init__()
        self.message_to_send = []
        self.chat_client = chat_client

    def run(self):
        # As long the client want to send message
        while len(self.message_to_send) > 0:
            # If the server don't send a response, wait
            if not self.chat_client.is_able_to_send_new_message:
                continue

            self.chat_client.send_message_from_thread(self.message_to_send[0])
            # Delete the message send
            self.message_to_send.pop(0)

            self.chat_client.is_able_to_send_new_message = False


class ChatClient(LoggingClass, QObject):

    def __init__(self):
        QObject.__init__(self)
        LoggingClass.__init__(self)

        self.socket = QLocalSocket()
        self.socket.readyRead.connect(self.handle_data_received)

        self.send_message_thread = SendMessageThread(self)

        self.is_able_to_send_new_message = True
        self.get_a_new_message = False
        self.get_message = None

    def connect_to_server(self, server_name="EMMIServer"):
        self.logger.debug("Connect client to the server")
        self.socket.connectToServer(server_name)

    def disconnect_from_server(self):
        self.socket.disconnectFromServer()

    def is_a_new_message_arrived(self) -> tuple[bool, str]:
        """
        Check if the client received a message
        :return bool: if the client has received a message
        :return str: the message received by the client
        """
        if self.get_a_new_message:
            self.get_a_new_message = False
            value_to_return = self.get_message
            self.get_message = None
            return True, value_to_return
        return False, ""

    def send_message(self, message):
        """
        :param message: Message to send to the server
        """
        if not self.is_connected:
            self.logger.warning("Try send message without be connected")
            return False

        self.send_message_thread.message_to_send.append(message)
        self.send_message_thread.start()
        return True

    def send_message_from_thread(self, message):
        """
        Send message only used by the thread SendMessageThread
        """
        message_to_send = message.encode('utf-8')
        self.socket.write(message_to_send)

        # Write message from the buffer to the socket
        self.socket.flush()
        self.logger.debug(f"Send message from client: {message}")

    def handle_data_received(self):
        """
        Call automatically if the server has a new message
        """
        try:
            data_received = self.socket.readAll().data().decode('utf-8')

            if data_received:
                self.logger.debug(f"Message received by the server to the client: {data_received}")

                # The server answer, so the client can send a new message
                self.is_able_to_send_new_message = True
                self.get_a_new_message = True
                self.get_message = data_received
            else:
                self.logger.error("Message send by the server is null")

        except Exception as e:
            self.logger.error(f"Error during lecture of server data: {e}")

    @property
    def is_connected(self):
        return self.socket.state() == QLocalSocket.LocalSocketState.ConnectedState


if __name__ == "__main__":
    local_client = ChatClient()

    handlerTerminal = logging.StreamHandler()
    handlerTerminal.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(levelname)s - %(thread)d - %(name)s - %(message)s")
    handlerTerminal.setFormatter(formatter)

    local_client.logger.addHandler(handlerTerminal)
    local_client.logger.setLevel(logging.DEBUG)