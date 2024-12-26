"""Database connection management module."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Dict, List, Any, Tuple, Union
from queue import Queue
from threading import Thread, Lock, Event
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Base exception for database operations."""
    pass

class DatabaseQueue:
    """Queue for handling database write operations."""
    
    def __init__(self, db: 'Database') -> None:
        """Initialize database queue.
        
        Args:
            db: Database instance to use for operations
        """
        self.db_path = db.db_path
        self.queue: Queue[Optional[Tuple[str, tuple, Event, Queue]]] = Queue()
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = Lock()
        self.worker = Thread(target=self._process_queue, daemon=True)
        self.running = True
        self.worker.start()
        logger.info("Database queue worker started")
    
    def _connect(self) -> None:
        """Create a dedicated database connection for the worker thread."""
        if not self._conn:
            try:
                self._conn = sqlite3.connect(self.db_path)
                self._conn.execute("PRAGMA foreign_keys = ON")
                self._conn.row_factory = sqlite3.Row
            except sqlite3.Error as e:
                self._conn = None
                raise DatabaseError(f"Queue worker failed to connect: {str(e)}")
    
    def _process_queue(self) -> None:
        """Process queued database operations."""
        try:
            self._connect()  # Create connection in worker thread
            
            while self.running:
                try:
                    item = self.queue.get()
                    if item is None:
                        break
                        
                    sql, params, completed_event, result_queue = item
                    
                    try:
                        with self._lock:
                            cursor = self._conn.execute(sql, params)
                            # For INSERT operations, get the last inserted row id
                            last_id = cursor.lastrowid if sql.strip().upper().startswith('INSERT') else None
                            self._conn.commit()
                            result_queue.put((True, last_id))
                    except Exception as e:
                        if self._conn:
                            self._conn.rollback()
                        logger.error(f"Error processing queued operation: {str(e)}")
                        result_queue.put((False, str(e)))
                    finally:
                        completed_event.set()
                        
                except Exception as e:
                    logger.error(f"Queue worker error: {str(e)}")
                    continue
                    
        finally:
            # Clean up connection when worker exits
            if self._conn:
                try:
                    self._conn.close()
                except sqlite3.Error:
                    pass
                self._conn = None
    
    def enqueue(self, sql: str, params: tuple = ()) -> Tuple[bool, Optional[Union[int, str]]]:
        """Enqueue a database operation.
        
        Args:
            sql: SQL query string
            params: Query parameters
            
        Returns:
            Tuple of (success: bool, result: Optional[Union[int, str]])
            For INSERT operations, result is the last inserted row id on success
            For failures, result is the error message string
        """
        completed_event = Event()
        result_queue: Queue[Tuple[bool, Optional[Union[int, str]]]] = Queue()
        
        self.queue.put((sql, params, completed_event, result_queue))
        completed_event.wait()  # Wait for operation to complete
        
        return result_queue.get()
    
    def shutdown(self) -> None:
        """Shutdown the queue worker."""
        self.running = False
        self.queue.put(None)  # Signal worker to stop
        self.worker.join()
        logger.info("Database queue worker shutdown")

from threading import local

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
        self._local = local()
        self._write_queue: Optional[DatabaseQueue] = None
        self._lock = Lock()
        
        # Create database directory if it doesn't exist
        if db_path:
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Only validate if file exists
            if Path(db_path).exists() and Path(db_path).stat().st_size > 0:
                try:
                    with sqlite3.connect(db_path) as test_conn:
                        test_conn.execute("SELECT 1")
                except sqlite3.Error as e:
                    raise DatabaseError(f"File exists but is not valid database: {str(e)}")
    
    @property
    def _conn(self) -> Optional[sqlite3.Connection]:
        """Get thread-local connection."""
        return getattr(self._local, 'conn', None)
    
    @_conn.setter
    def _conn(self, value: Optional[sqlite3.Connection]) -> None:
        """Set thread-local connection."""
        self._local.conn = value

    def connect(self) -> None:
        """Establish database connection.
        
        Creates a new connection for the current thread if one doesn't exist.
        
        Raises:
            DatabaseError: If connection fails.
        """
        with self._lock:
            if not self._conn:
                try:
                    conn = sqlite3.connect(self.db_path)
                    # Enable foreign key constraints
                    conn.execute("PRAGMA foreign_keys = ON")
                    conn.row_factory = sqlite3.Row
                    self._conn = conn
                    
                    # Initialize write queue if not exists
                    if not self._write_queue:
                        self._write_queue = DatabaseQueue(self)
                except (sqlite3.Error, OSError) as e:
                    self._conn = None
                    raise DatabaseError(f"Failed to connect to database: {str(e)}")
    
    def disconnect(self) -> None:
        """Close database connection for the current thread.
        
        Raises:
            DatabaseError: If disconnection fails.
        """
        with self._lock:
            if self._write_queue:
                self._write_queue.shutdown()
                self._write_queue = None
                
            conn = self._conn
            if conn:
                try:
                    conn.close()
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
    
    def execute(self, query: str, params: tuple = ()) -> Optional[int]:
        """Execute a database query.
        
        Args:
            query: SQL query string.
            params: Query parameters.
            
        Returns:
            For INSERT operations, returns the last inserted row id.
            For other operations, returns None.
            
        Raises:
            DatabaseError: If query execution fails.
        """
        if not self._conn:
            self.connect()
        
        # Use queue for write operations
        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
            if not self._write_queue:
                raise DatabaseError("Write queue not initialized")
                
            success, result = self._write_queue.enqueue(query, params)
            if not success:
                raise DatabaseError(f"Query execution failed: {result}")
            return result if isinstance(result, int) else None
            
        # Direct execution for read operations
        try:
            with self.transaction() as conn:
                conn.execute(query, params)
            return None
        except DatabaseError as e:
            raise DatabaseError(f"Query execution failed: {str(e)}")
    
    def executescript(self, script: str) -> None:
        """Execute a SQL script containing multiple statements.
        
        Args:
            script: SQL script string containing one or more statements.
            
        Raises:
            DatabaseError: If script execution fails.
        """
        if not self._conn:
            self.connect()
            
        try:
            with self.transaction() as conn:
                conn.executescript(script)
        except DatabaseError as e:
            raise DatabaseError(f"Script execution failed: {str(e)}")
    
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

    async def get_repositories(self) -> List[Dict[str, Any]]:
        """Get all repositories from the database.
        
        Returns:
            List of repository dictionaries.
            
        Raises:
            DatabaseError: If query fails.
        """
        try:
            rows = self.fetch_all(
                """
                SELECT r.*, GROUP_CONCAT(rc.topic_id) as topic_ids,
                       GROUP_CONCAT(rc.confidence_score) as confidence_scores
                FROM repositories r
                LEFT JOIN repository_categories rc ON r.id = rc.repository_id
                GROUP BY r.id
                """
            )
            
            # Convert rows to dictionaries and process topic relationships
            repositories = []
            for row in rows:
                repo_dict = dict(row)
                
                # Process topic relationships
                topic_ids = row['topic_ids']
                confidence_scores = row['confidence_scores']
                
                if topic_ids and confidence_scores:
                    topic_ids = [int(id) for id in topic_ids.split(',')]
                    confidence_scores = [float(score) for score in confidence_scores.split(',')]
                    repo_dict['topics'] = [
                        {'topic_id': tid, 'confidence_score': score}
                        for tid, score in zip(topic_ids, confidence_scores)
                    ]
                else:
                    repo_dict['topics'] = []
                
                repositories.append(repo_dict)
            
            return repositories
            
        except Exception as e:
            raise DatabaseError(f"Failed to get repositories: {str(e)}")

    async def get_topics(self) -> Dict[int, Dict[str, Any]]:
        """Get all topics from the database.
        
        Returns:
            Dictionary mapping topic IDs to topic data.
            
        Raises:
            DatabaseError: If query fails.
        """
        try:
            rows = self.fetch_all("SELECT * FROM topics")
            
            # Convert to dictionary keyed by topic ID
            return {row['id']: dict(row) for row in rows}
            
        except Exception as e:
            raise DatabaseError(f"Failed to get topics: {str(e)}")

@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Get a database connection for use in a context manager.
    
    This function provides a convenient way to get a database connection
    that will be automatically closed when the context is exited.
    
    Yields:
        sqlite3.Connection: Active database connection
        
    Example:
        with get_db_connection() as conn:
            result = conn.execute("SELECT * FROM table").fetchall()
    """
    db = Database()
    db.connect()
    try:
        yield db._conn
        db._conn.commit()
    except Exception:
        if db._conn:
            db._conn.rollback()
        raise
    finally:
        db.disconnect()
