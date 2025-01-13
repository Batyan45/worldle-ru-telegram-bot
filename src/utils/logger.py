"""Logging configuration for the application."""

import logging
from pathlib import Path
from typing import Optional

from src.config.settings import GAME_LOGS_FILE


def setup_logger(log_file: Optional[Path] = None) -> tuple[logging.Logger, logging.Logger]:
    """
    Set up loggers for the application.
    
    Args:
        log_file: Optional path to the log file. Defaults to 'game_logs.log'.
        
    Returns:
        tuple: A tuple containing (game_logger, system_logger).
    """
    # Create a separate logger for the game
    game_logger = logging.getLogger('game')
    game_logger.setLevel(logging.INFO)

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Create handlers
    log_file = log_file or Path(GAME_LOGS_FILE)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    game_logger.addHandler(file_handler)

    # Disable log propagation to parent logger
    game_logger.propagate = False

    # Basic setup for system logs
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    system_logger = logging.getLogger('system')
    
    return game_logger, system_logger 