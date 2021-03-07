import os
import logging
from tempfile import gettempdir

__all__ = ["get_logger"]


def get_logger(name: str = "") -> logging.Logger:
    logger = logging.getLogger(f"panwid-{name}")
    logger.setLevel(logging.DEBUG)
    log_file = os.path.join(gettempdir(), f"panwid-{name}.log")

    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setLevel(logging.DEBUG)

    format = "[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    formatter = logging.Formatter(format)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger
