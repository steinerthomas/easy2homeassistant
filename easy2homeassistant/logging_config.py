"""Module for logging configuration."""

import logging
import sys

import colorlog

LOG_COLORS = {
    "DEBUG": "light_black",
    "INFO": "black",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}
LOGGER_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE_PATH = "easy2homeassistant.log"


def configure_logging(logging_level="INFO"):
    """Return a logger with the specified name."""
    console_handler = colorlog.StreamHandler(sys.stdout)
    console_formatter = colorlog.ColoredFormatter(
        f"%(log_color)s{LOGGER_FORMAT}", log_colors=LOG_COLORS
    )
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler(LOG_FILE_PATH)
    file_formatter = logging.Formatter(LOGGER_FORMAT)
    file_handler.setFormatter(file_formatter)

    logging.basicConfig(handlers=[console_handler, file_handler])


def set_logging_level(logging_level):
    """Set the logging level for the root logger."""
    logging.root.setLevel(logging_level)
