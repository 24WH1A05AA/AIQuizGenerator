"""Centralised logging for AIQuizGenerator.

Technical details go to quiz_generator.log (rotating, 5 MB × 3 backups).
Nothing from this module is shown to the user.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_FILE = os.path.join(os.path.dirname(__file__), "quiz_generator.log")

def _build_logger() -> logging.Logger:
    logger = logging.getLogger("aiquizgenerator")
    if logger.handlers:          # already configured (Streamlit reruns)
        return logger
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Rotating file handler
    fh = RotatingFileHandler(_LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


log = _build_logger()
