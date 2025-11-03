from threading import Lock
from Scripts.Translation_stage.translation_stage_pi import TranslationPi
from PyQt6.QtCore import QMutexLocker, QMutex


class TranslationStageInterface(TranslationPi):
    """
    Singleton class
    Interface between TranslationPi and Qt to handle multithreading.
    A mutex locks the access to methods.
    Thread-safe singleton implementation.
    """
    _instance = None
    _lock = Lock()  # Thread safety
    _initialized = False

    def __new__(cls, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TranslationPi, cls).__new__(cls)
        return cls._instance

    def __init__(self, **kwargs):
        with self._lock:
            if not self._initialized:
                self._mutex = QMutex()
                super().__init__(**kwargs)
                self._initialized = True

    @classmethod
    def get_instance(cls, **kwargs):
        """
        Return the reference of the instance
        """
        return cls(**kwargs) # Call __new__ then __init__

    def ask(self, msg: str, data_size_received=None) -> str:
        with QMutexLocker(self._mutex):
            return TranslationPi.ask(self, msg, data_size_received)

    def write(self, msg: str):
        with QMutexLocker(self._mutex):
            return TranslationPi.write(self, msg)
