"""Setup logging for the application."""

import logging

# import os
import sys
from .config import LOG_FILE_PATH, ASR_CONFIG


def setup_logging(logger_name="ASR_app"):
    """Initialize and configure the application logger."""

    log_file = LOG_FILE_PATH[logger_name]

    # Create logger
    log_level = ASR_CONFIG["log_level"].upper()
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Prevent logs from being duplicated in other loggers
    logger.propagate = False

    # Remove existing handlers (to prevent duplicate logs)
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])

    # Create file handlers
    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setLevel(logging.DEBUG if log_level == "DEBUG" else logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)

    # Create formatter and add it to the handlers
    if log_level == "DEBUG":
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(funcName)s -\t %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Logging initialized. Logging to %s", LOG_FILE_PATH[logger_name])

    return logger


logger = setup_logging()
