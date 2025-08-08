import logging
import sys
from typing import Optional

from app.core.config import settings


def setup_logger(name: str = "queryiq") -> logging.Logger:
    """Set up and configure logger for the application."""
    
    logger = logging.getLogger(name)
    
    if logger.handlers:  # Avoid adding handlers multiple times
        return logger
    
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


# Global logger instance
logger = setup_logger() 