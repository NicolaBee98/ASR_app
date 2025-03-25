"""Setup logging for the application."""

import logging

# import os
import sys
from .config import LOG_FILE_PATH, ASR_CONFIG


def setup_logging():
    """Initialize and configure the application logger."""
    # Create logger
    log_level = ASR_CONFIG["log_level"].upper()
    logger = logging.getLogger("audio_recorder")
    logger.setLevel(log_level)
    # Create file handler
    file_handler = logging.FileHandler(LOG_FILE_PATH, mode="w")
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

    logger.info("Logging initialized. Logging to %s", LOG_FILE_PATH)

    return logger


logger = setup_logging()
