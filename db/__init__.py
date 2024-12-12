"""Database package initialization."""

import os
from pathlib import Path
from typing import Optional

from db.connection import Database, DatabaseError
from db.migrations import MigrationManager

# Default to a database file in the db directory
DEFAULT_DB_PATH = os.path.join(
    Path(__file__).parent.parent,
    "data",
    "newsletter_curator.db"
)

def init_database(db_path: Optional[str] = None) -> Database:
    """Initialize database with schema.
    
    Args:
        db_path: Path to SQLite database file. If None, uses default path.
        
    Returns:
        Initialized Database instance.
        
    Raises:
        DatabaseError: If initialization fails.
    """
    db = Database(db_path or DEFAULT_DB_PATH)
    
    try:
        # Ensure database connection
        db.connect()
        
        # Apply migrations
        manager = MigrationManager(db)
        manager.apply_migrations()
        
        return db
    except Exception as e:
        raise DatabaseError(f"Failed to initialize database: {str(e)}")

__all__ = ['Database', 'DatabaseError', 'init_database']
