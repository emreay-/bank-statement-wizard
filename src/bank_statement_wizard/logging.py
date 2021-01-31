import os
import logging
from tempfile import gettempdir

__all__ = ["get_logger"]


def get_logger() -> logging.Logger:
    logger = logging.getLogger("bank_statement_wizard")
    logger.setLevel(logging.DEBUG)
    log_file = os.path.join(gettempdir(), "bank_statement_wizard.log")
    remove_if_exists(log_file)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s")
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger


def remove_if_exists(path: str):
    if os.path.exists(path):
        os.remove(path)
