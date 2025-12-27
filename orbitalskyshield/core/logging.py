# Author: Andres Espin
# Email: aaespin3@espe.edu.ec
# Role: Junior Developer
# Purpose: Independent Research Study

import logging
import sys
from typing import Optional

def setup_logging(
    name: str = "orbitalskyshield",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """Configures and returns a logger."""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Check if handlers already exist to avoid duplicates
    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def get_logger(name: str = "orbitalskyshield") -> logging.Logger:
    return logging.getLogger(name)
