from typing import Optional
from threading import Lock

from PyQt6.QtCore import QMutexLocker, QMutex
from Scripts.Camera.raptor_ninox640II import RaptorNinox640II

class CameraInterface(RaptorNinox640II):
    """
    Singleton class
    Interface between RaptorNinox640II and Qt to handle multithreading.
    A mutex locks the access to methods.
    Thread-safe singleton implementation.
    """
    _instance = None
    _lock = Lock()  # Thread safety
    _initialized = False

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CameraInterface, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        with self._lock:
            if not self._initialized:
                self._mutex = QMutex()
                super().__init__()
                self._initialized = True

    @classmethod
    def get_instance(cls):
        """
        Return the reference of the instance
        """
        return cls()  # Call __new__ then __init__

    def serial_set(self, data: list, length_answer: Optional[int] = 2):
        with QMutexLocker(self._mutex):
            return super().serial_set(data, length_answer)

    def serial_get(self, data: list, length_answer):
        with QMutexLocker(self._mutex):
            return super().serial_get(data, length_answer)

