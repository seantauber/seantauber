import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(name: str) -> logging.Logger:
    """Set up logging configuration for the application.
    
    Args:
        name: The name of the logger/module
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Create file handler for application logs
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(
        filename=f"logs/{name}_{current_time}.log"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Set up CrewAI related logging
    crewai_logger = logging.getLogger('crewai')
    crewai_logger.setLevel(logging.DEBUG)
    
    # Create file handler for CrewAI logs
    crewai_file_handler = logging.FileHandler(
        filename=f"logs/crewai_{current_time}.log"
    )
    crewai_file_handler.setLevel(logging.DEBUG)
    crewai_file_handler.setFormatter(file_formatter)
    crewai_logger.addHandler(crewai_file_handler)
    
    # Add console handler for CrewAI logger
    crewai_console_handler = logging.StreamHandler(sys.stdout)
    crewai_console_handler.setLevel(logging.INFO)
    crewai_console_handler.setFormatter(console_formatter)
    crewai_logger.addHandler(crewai_console_handler)
    
    return logger
