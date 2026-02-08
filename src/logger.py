"""
Logger module for AI Terminal Assistant.
Logs all actions, commands, and events to the command history log file.
"""

import os
import logging
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "command_history.log")


def _ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def get_logger(name="assistant"):
    """Get a configured logger instance."""
    _ensure_log_dir()

    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)

        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(fmt)
        console_handler.setFormatter(fmt)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


def log_action(action_name, details="", success=True):
    """Log an action execution to the history file."""
    logger = get_logger()
    status = "SUCCESS" if success else "FAILED"
    logger.info("ACTION  | %-15s | %s | %s", action_name, status, details)


def log_command(command, approved=True, output=""):
    """Log a terminal command execution."""
    logger = get_logger()
    status = "APPROVED" if approved else "REJECTED"
    logger.info("COMMAND | %s | %s | output=%s", command, status, output[:200])


def log_event(event, details=""):
    """Log a general event."""
    logger = get_logger()
    logger.info("EVENT   | %s | %s", event, details)
