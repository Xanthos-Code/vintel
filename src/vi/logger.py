
import logging
import logging.handlers

from vi.singleton import Singleton

gLogLevel = logging.DEBUG

class Logger:

    __metaclass__ = Singleton

    def __init__(self, outputDirectory):
        # Setup loggging for console and log files, which are rotated
        logFilename = outputDirectory + "/output.txt"
        rootLogger = logging.getLogger()
        logFormatter = logging.Formatter('%(asctime)s| %(message)s', datefmt='%m/%d %I:%M:%S %p')

        fileHandler = logging.handlers.RotatingFileHandler(maxBytes=(1048576*5), backupCount=7, filename=logFilename, mode='a')
        fileHandler.setFormatter(logFormatter)
        fileHandler.setLevel(gLogLevel)
        rootLogger.addHandler(fileHandler)

        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        consoleHandler.setLevel(gLogLevel)
        rootLogger.addHandler(consoleHandler)

        self.fileHandler = fileHandler
        self.consoleHandler = consoleHandler
        self.levelStack = []

    def debug(self, message):
        logging.debug(message)

    def info(self, message):
        logging.info(message)

    def warning(self, message):
        logging.warning(message)

    def error(self, message):
        logging.error(message)

    def critical(self, message):
        logging.critical(message)

    def exception(self, message):
        logging.exception(message)

    def pushLevel(self, level):
        self.levelStack.append(self.fileHandler.level)
        self.fileHandler.setLevel(level)
        self.consoleHandler.setLevel(level)

    def popLevel(self):
        level = self.levelStack.pop()
        if not level:
            level = gLogLevel
        self.fileHandler.setLevel(level)
        self.consoleHandler.setLevel(level)
