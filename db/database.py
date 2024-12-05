import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from models.github_repo_data import GitHubRepoData

class DatabaseManager:
    """Manages database operations for storing and retrieving GitHub repository data."""
    
    def __init__(self, db_path: str = "db/github_repos.db"):
        """Initialize database connection and create tables if they don't exist.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        # Ensure the database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """Initialize the database by creating necessary tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create raw_repositories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raw_repositories (
                    id INTEGER PRIMARY KEY,
                    source TEXT NOT NULL,
                    data JSON NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    batch_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create analyzed_repositories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analyzed_repositories (
                    id INTEGER PRIMARY KEY,
                    raw_repo_id INTEGER,
                    analysis_data JSON NOT NULL,
                    batch_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (raw_repo_id) REFERENCES raw_repositories(id)
                )
            """)
            
            # Create batch_processing table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS batch_processing (
                    id INTEGER PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    batch_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error TEXT,
                    CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
                )
            """)
            
            conn.commit()
    
    def store_raw_repos(self, repos: List[GitHubRepoData], source: str, batch_id: Optional[int] = None):
        """Store raw repository data in the database.
        
        Args:
            repos (List[GitHubRepoData]): List of GitHubRepoData objects
            source (str): Source of the repositories ('starred' or 'trending')
            batch_id (Optional[int]): ID of the processing batch
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for repo in repos:
                # Convert GitHubRepoData to dict and then to JSON
                repo_dict = repo.dict()
                cursor.execute(
                    """
                    INSERT INTO raw_repositories (source, data, batch_id)
                    VALUES (?, ?, ?)
                    """,
                    (source, json.dumps(repo_dict), batch_id)
                )
            conn.commit()
    
    def get_unprocessed_repos(self, batch_size: int = 10) -> List[Dict]:
        """Retrieve a batch of unprocessed repositories.
        
        Args:
            batch_size (int): Number of repositories to retrieve
            
        Returns:
            List[Dict]: List of unprocessed repository data
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, data FROM raw_repositories
                WHERE processed = FALSE
                LIMIT ?
                """,
                (batch_size,)
            )
            results = cursor.fetchall()
            return [{'id': row[0], 'data': json.loads(row[1])} for row in results]
    
    def store_analyzed_repos(self, analyzed_repos: List[Dict], batch_id: Optional[int] = None):
        """Store analyzed repository data and mark raw repos as processed.
        
        Args:
            analyzed_repos (List[Dict]): List of analyzed repository data
            batch_id (Optional[int]): ID of the processing batch
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for repo in analyzed_repos:
                # Store analyzed data
                cursor.execute(
                    """
                    INSERT INTO analyzed_repositories (raw_repo_id, analysis_data, batch_id)
                    VALUES (?, ?, ?)
                    """,
                    (repo['raw_repo_id'], json.dumps(repo['analysis_data']), batch_id)
                )
                
                # Mark raw repo as processed
                cursor.execute(
                    """
                    UPDATE raw_repositories
                    SET processed = TRUE
                    WHERE id = ?
                    """,
                    (repo['raw_repo_id'],)
                )
            conn.commit()
    
    def get_analyzed_repos(self) -> List[Dict]:
        """Retrieve all analyzed repositories.
        
        Returns:
            List[Dict]: List of analyzed repository data
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT r.source, a.analysis_data
                FROM analyzed_repositories a
                JOIN raw_repositories r ON r.id = a.raw_repo_id
                ORDER BY a.created_at DESC
                """
            )
            results = cursor.fetchall()
            return [{'source': row[0], 'analysis_data': json.loads(row[1])} for row in results]

    def create_batch(self, task_type: str) -> int:
        """Create a new batch processing record.
        
        Args:
            task_type (str): Type of task ('fetch', 'analyze', etc.)
            
        Returns:
            int: ID of the created batch
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO batch_processing (task_type, batch_id, status, started_at)
                VALUES (?, (
                    SELECT COALESCE(MAX(batch_id) + 1, 1)
                    FROM batch_processing
                    WHERE task_type = ?
                ), 'pending', CURRENT_TIMESTAMP)
                """,
                (task_type, task_type)
            )
            conn.commit()
            return cursor.lastrowid

    def update_batch_status(self, batch_id: int, status: str, error: Optional[str] = None):
        """Update the status of a batch processing record.
        
        Args:
            batch_id (int): ID of the batch to update
            status (str): New status ('pending', 'processing', 'completed', 'failed')
            error (Optional[str]): Error message if status is 'failed'
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if status == 'completed' or status == 'failed':
                cursor.execute(
                    """
                    UPDATE batch_processing
                    SET status = ?, completed_at = CURRENT_TIMESTAMP, error = ?
                    WHERE id = ?
                    """,
                    (status, error, batch_id)
                )
            else:
                cursor.execute(
                    """
                    UPDATE batch_processing
                    SET status = ?
                    WHERE id = ?
                    """,
                    (status, batch_id)
                )
            conn.commit()

    def get_batch_status(self, task_type: str) -> Dict[int, Dict]:
        """Get status of all batches for a task type.
        
        Args:
            task_type (str): Type of task to get status for
            
        Returns:
            Dict[int, Dict]: Dictionary of batch IDs to their status information
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT batch_id, status, started_at, completed_at, error
                FROM batch_processing
                WHERE task_type = ?
                ORDER BY batch_id
                """,
                (task_type,)
            )
            results = cursor.fetchall()
            return {
                row[0]: {
                    'status': row[1],
                    'started_at': row[2],
                    'completed_at': row[3],
                    'error': row[4]
                }
                for row in results
            }
