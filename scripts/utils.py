"""Common utilities for pipeline scripts."""

import os
import logging
from typing import List, Optional
from datetime import datetime

def setup_logging(stage_name: str) -> logging.Logger:
    """
    Set up logging configuration for a pipeline stage.
    
    Args:
        stage_name: Name of the pipeline stage for log formatting
        
    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=logging.INFO,
        format=f'%(asctime)s - {stage_name} - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('pipeline.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def validate_environment(required_vars: Optional[List[str]] = None) -> None:
    """
    Validate required environment variables.
    
    Args:
        required_vars: List of required variable names. If None, checks default set.
        
    Raises:
        ValueError: If any required variables are missing
    """
    if required_vars is None:
        required_vars = [
            "OPENAI_API_KEY",
            "GMAIL_CREDENTIALS_PATH",
            "GMAIL_TOKEN_PATH",
            "GMAIL_LABEL",
            "GITHUB_TOKEN",
            "DATABASE_PATH",
            "VECTOR_STORE_PATH",
            "REDIS_URL"
        ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to split
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def format_duration(start_time: datetime) -> str:
    """
    Format duration since start time.
    
    Args:
        start_time: Starting datetime
        
    Returns:
        Formatted duration string
    """
    duration = datetime.now() - start_time
    seconds = duration.total_seconds()
    
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
