import logging

class LoggingClass:
    def __init__(self):
        c = self.__class__
        if c.__module__ in ['__main__', 'builtins']:
            self.logger = logging.getLogger(c.__qualname__)
        else:
            self.logger = logging.getLogger(c.__module__ + '.' + c.__qualname__)
