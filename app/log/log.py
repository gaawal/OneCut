import sys

from loguru import logger as loguru_logger

from app.settings import base_settings


class Loggin:
    def __init__(self) -> None:
        debug = base_settings.DEBUG
        if debug:
            self.level = "DEBUG"
        else:
            self.level = "INFO"

    def setup_logger(self):
        loguru_logger.remove()
        loguru_logger.add(sink=sys.stdout, level=self.level,
                          format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
                                 "| <level>{level}</level> "
                                 "| <cyan>{name}</cyan> "
                                 "| <blue>{function}</blue> "
                                 "| <yellow>{line}</yellow> "
                                 " - <level>{message}</level>")

        logger.add("cut.log", level=self.level, rotation="100 MB")  # Output log messages to a file
        return loguru_logger


loggin = Loggin()
logger = loggin.setup_logger()
