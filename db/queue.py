"""Queue-based database operations for safe concurrent writes."""

import logging
import queue
import threading
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, UTC

from db.connection import Database

logger = logging.getLogger(__name__)

class DatabaseQueue:
    """Queue for safe concurrent database operations."""
    
    def __init__(self, db: Database):
        """Initialize database queue.
        
        Args:
            db: Database connection to use
        """
        self.db = db
        self.queue = queue.Queue()
        self.results: Dict[str, Any] = {}
        self.worker = threading.Thread(target=self._process_queue, daemon=True)
        self.worker.start()
        
    def _process_queue(self):
        """Process queued database operations."""
        while True:
            try:
                # Get next operation from queue
                operation = self.queue.get()
                if operation is None:  # Shutdown signal
                    break
                    
                batch_id, sql, params, result_key = operation
                
                try:
                    with self.db.transaction() as conn:
                        cursor = conn.execute(sql, params)
                        
                        if result_key:
                            if sql.strip().upper().startswith('SELECT'):
                                # Store query results
                                self.results[result_key] = [dict(row) for row in cursor.fetchall()]
                            else:
                                # Store last row id for inserts
                                self.results[result_key] = cursor.lastrowid
                                
                except Exception as e:
                    logger.error(f"Database operation failed for batch {batch_id}: {str(e)}")
                    self.results[f"error_{batch_id}"] = str(e)
                    
                finally:
                    self.queue.task_done()
                    
            except Exception as e:
                logger.error(f"Queue processing error: {str(e)}")
                continue
    
    def enqueue(
        self,
        batch_id: str,
        sql: str,
        params: Tuple = (),
        result_key: Optional[str] = None
    ):
        """Add database operation to queue.
        
        Args:
            batch_id: Identifier for the batch this operation belongs to
            sql: SQL statement to execute
            params: Query parameters
            result_key: Optional key to store operation result
        """
        self.queue.put((batch_id, sql, params, result_key))
    
    def get_result(self, key: str, timeout: float = 5.0) -> Any:
        """Get result of database operation.
        
        Args:
            key: Result key to retrieve
            timeout: How long to wait for result in seconds
            
        Returns:
            Operation result if available
            
        Raises:
            queue.Empty: If result not available within timeout
        """
        self.queue.join()  # Wait for all operations to complete
        return self.results.get(key)
    
    def shutdown(self):
        """Shutdown queue worker."""
        self.queue.put(None)  # Send shutdown signal
        self.worker.join()
