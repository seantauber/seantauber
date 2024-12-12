"""Database connection management module."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

class DatabaseError(Exception):
    """Base exception for database operations."""
    pass

class Database:
    """SQLite database connection manager."""
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize database connection manager.
        
        Args:
            db_path: Path to SQLite database file. If None, uses in-memory database.
            
        Raises:
            DatabaseError: If database file exists but is not valid.
        """
        self.db_path = db_path or ":memory:"
        self._conn: Optional[sqlite3.Connection] = None
        
        # Create database directory if it doesn't exist
        if db_path:
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Validate database file if it exists
            if Path(db_path).exists():
                # Check SQLite header magic string
                with open(db_path, "rb") as f:
                    header = f.read(16)
                    if not header.startswith(b"SQLite format 3"):
                        raise DatabaseError("File exists but is not a valid database")
                
                # If header looks valid, try connecting
                try:
                    with sqlite3.connect(db_path) as test_conn:
                        test_conn.execute("SELECT 1")
                except sqlite3.Error as e:
                    raise DatabaseError("File exists but is not a valid database")
    
    def connect(self) -> None:
        """Establish database connection.
        
        Raises:
            DatabaseError: If connection fails.
        """
        try:
            self._conn = sqlite3.connect(self.db_path)
            # Enable foreign key constraints
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.row_factory = sqlite3.Row
        except (sqlite3.Error, OSError) as e:
            self._conn = None
            raise DatabaseError(f"Failed to connect to database: {str(e)}")
    
    def disconnect(self) -> None:
        """Close database connection.
        
        Raises:
            DatabaseError: If disconnection fails.
        """
        if self._conn:
            try:
                self._conn.close()
                self._conn = None
            except sqlite3.Error as e:
                raise DatabaseError(f"Failed to close database connection: {str(e)}")
    
    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database transactions.
        
        Yields:
            Active database connection.
            
        Raises:
            DatabaseError: If transaction operations fail.
        """
        if not self._conn:
            self.connect()
            
        try:
            yield self._conn
            self._conn.commit()
        except sqlite3.Error as e:
            if self._conn:
                self._conn.rollback()
            raise DatabaseError(f"Transaction failed: {str(e)}")
    
    def execute(self, query: str, params: tuple = ()) -> None:
        """Execute a database query.
        
        Args:
            query: SQL query string.
            params: Query parameters.
            
        Raises:
            DatabaseError: If query execution fails.
        """
        if not self._conn:
            self.connect()
            
        try:
            with self.transaction() as conn:
                conn.execute(query, params)
        except DatabaseError as e:
            raise DatabaseError(f"Query execution failed: {str(e)}")
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Fetch a single row from the database.
        
        Args:
            query: SQL query string.
            params: Query parameters.
            
        Returns:
            Single database row or None if no results.
            
        Raises:
            DatabaseError: If query execution fails.
        """
        if not self._conn:
            self.connect()
            
        try:
            with self.transaction() as conn:
                cursor = conn.execute(query, params)
                return cursor.fetchone()
        except DatabaseError as e:
            raise DatabaseError(f"Failed to fetch row: {str(e)}")
    
    def fetch_all(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Fetch all rows from the database.
        
        Args:
            query: SQL query string.
            params: Query parameters.
            
        Returns:
            List of database rows.
            
        Raises:
            DatabaseError: If query execution fails.
        """
        if not self._conn:
            self.connect()
            
        try:
            with self.transaction() as conn:
                cursor = conn.execute(query, params)
                return cursor.fetchall()
        except DatabaseError as e:
            raise DatabaseError(f"Failed to fetch rows: {str(e)}")
