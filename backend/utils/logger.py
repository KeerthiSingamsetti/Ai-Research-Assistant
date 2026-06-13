import os
import logging
from backend.config import settings

def setup_logger(name: str) -> logging.Logger:
    """Sets up and configures a logger instance with console and file handlers.

    Args:
        name: Name of the logger.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicating handlers if logger is already configured
    if logger.handlers:
        return logger

    # Set logger level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Format configuration
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    formatter = logging.Formatter(log_format)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    file_path = os.path.join(logs_dir, "app.log")
    
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
