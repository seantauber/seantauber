import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from models.github_repo_data import GitHubRepoData, AnalyzedRepoData, CombinedRepoData
from models.flow_state import FlowState, RepoProcessingState, RepoAnalysis, ReadmeState

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class DatabaseManager:
    """Manages database operations for storing and retrieving GitHub repository data.
    
    This class implements the singleton pattern to ensure only one instance exists
    across the application, preventing unintended database cleanups.
    """
    
    _instance = None
    _initialized = False
    _state = {
        'connection_active': False,
        'tables_initialized': False,
        'last_operation': None,
        'last_operation_time': None
    }
    
    def __new__(cls, *args, **kwargs):
        """Ensure only one instance of DatabaseManager exists."""
        # Add call stack logging to track where DatabaseManager is being instantiated
        import traceback
        caller_info = traceback.extract_stack()[-2]  # Get caller information
        
        if cls._instance is None:
            logger.info(f"Creating new DatabaseManager instance from {caller_info.filename}:{caller_info.lineno}")
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        else:
            logger.debug(f"Returning existing DatabaseManager instance (called from {caller_info.filename}:{caller_info.lineno})")
        return cls._instance

    def __init__(self, db_path: str = "db/github_repos.db", cleanup: bool = False):
        """Initialize database connection and create tables if they don't exist.
        
        Args:
            db_path (str): Path to the SQLite database file
            cleanup (bool): Whether to clean up existing data on initialization (default: False)
        """
        # Add call stack logging to track where initialization is happening
        import traceback
        caller_info = traceback.extract_stack()[-2]  # Get caller information
        
        # Only initialize once
        if not self._initialized:
            logger.info(f"Initializing DatabaseManager from {caller_info.filename}:{caller_info.lineno}")
            
            if cleanup:
                logger.warning(f"Cleanup requested during initialization from {caller_info.filename}:{caller_info.lineno}")
            
            self.db_path = db_path
            logger.debug(f"Database file exists: {Path(db_path).exists()}")
            
            # Ensure the database directory exists
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize database first
            self.init_db()
            
            # Then clean up if requested
            if cleanup:
                self.cleanup_database()
            
            self._initialized = True
            logger.info("DatabaseManager initialization completed")
        else:
            logger.debug(f"Skipping initialization for existing instance (called from {caller_info.filename}:{caller_info.lineno})")

    def _update_state(self, operation: str):
        """Update the internal state of the DatabaseManager.
        
        Args:
            operation (str): The name of the operation being performed
        """
        self._state['last_operation'] = operation
        self._state['last_operation_time'] = datetime.now()
        logger.debug(f"State updated - Operation: {operation}, Time: {self._state['last_operation_time']}")

    def cleanup_database(self):
        """Clean up the database by removing all existing data from tables."""
        logger.info("Starting database cleanup")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Start transaction
                cursor.execute("BEGIN TRANSACTION")
                
                try:
                    # Delete all data from tables in reverse order of dependencies
                    cursor.execute("DELETE FROM analyzed_repositories")
                    cursor.execute("DELETE FROM raw_repositories")
                    cursor.execute("DELETE FROM batch_processing")
                    cursor.execute("DELETE FROM flow_state")
                    
                    # Reset auto-increment counters
                    cursor.execute("DELETE FROM sqlite_sequence")
                    
                    # Commit transaction
                    conn.commit()
                    logger.info("Database cleanup completed successfully")
                    self._update_state('cleanup_database')
                    
                except Exception as e:
                    # Rollback on error
                    conn.rollback()
                    logger.error(f"Error in cleanup_database transaction: {e}")
                    raise
                
        except sqlite3.Error as e:
            logger.error(f"Database error in cleanup_database: {e}")
            raise

    def init_db(self):
        """Initialize the database by creating necessary tables if they don't exist."""
        logger.info("Initializing database tables")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Enable foreign key support
                cursor.execute("PRAGMA foreign_keys = ON")
                logger.debug("Enabled foreign key support")
                
                # Create raw_repositories table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS raw_repositories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT NOT NULL,
                        data JSON NOT NULL,
                        processed BOOLEAN DEFAULT FALSE,
                        batch_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.debug("Created/verified raw_repositories table")
                
                # Create analyzed_repositories table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analyzed_repositories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        raw_repo_id INTEGER NOT NULL,
                        analysis_data JSON NOT NULL,
                        batch_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (raw_repo_id) REFERENCES raw_repositories(id)
                    )
                """)
                logger.debug("Created/verified analyzed_repositories table")
                
                # Create batch_processing table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS batch_processing (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_type TEXT NOT NULL,
                        batch_id INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        error TEXT,
                        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'retry_queue', 'cleaned_up'))
                    )
                """)
                logger.debug("Created/verified batch_processing table")

                # Create flow_state table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS flow_state (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        state_data JSON NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_latest BOOLEAN DEFAULT TRUE
                    )
                """)
                logger.debug("Created/verified flow_state table")
                
                conn.commit()
                logger.debug("Database initialization transaction committed successfully")
                logger.info("Database initialized successfully")
                
                self._state['tables_initialized'] = True
                self._update_state('init_db')
                
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            self._state['connection_active'] = False
            raise

    def get_unprocessed_repos(self, batch_size: int = 10) -> List[Dict]:
        """Get a batch of unprocessed repositories from the database.
        
        Args:
            batch_size (int): Number of repositories to retrieve (default: 10)
            
        Returns:
            List[Dict]: List of unprocessed repository data
        """
        logger.info(f"Getting {batch_size} unprocessed repositories")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get unprocessed repos
                cursor.execute("""
                    SELECT data
                    FROM raw_repositories
                    WHERE processed = FALSE
                    LIMIT ?
                """, (batch_size,))
                
                results = cursor.fetchall()
                repos = [json.loads(row[0]) for row in results]
                logger.info(f"Retrieved {len(repos)} unprocessed repositories")
                return repos
                
        except sqlite3.Error as e:
            logger.error(f"Database error in get_unprocessed_repos: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing repository data: {e}")
            return []

    def get_analyzed_repos(self) -> List[Dict]:
        """Get all analyzed repositories from the database.
        
        Returns:
            List[Dict]: List of analyzed repository data
        """
        logger.info("Getting all analyzed repositories")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get analyzed repos with their raw data
                cursor.execute("""
                    SELECT r.data, a.analysis_data
                    FROM raw_repositories r
                    JOIN analyzed_repositories a ON r.id = a.raw_repo_id
                """)
                
                results = cursor.fetchall()
                repos = []
                for raw_data, analysis_data in results:
                    repo_data = json.loads(raw_data)
                    repo_data.update(json.loads(analysis_data))
                    repos.append(repo_data)
                
                logger.info(f"Retrieved {len(repos)} analyzed repositories")
                return repos
                
        except sqlite3.Error as e:
            logger.error(f"Database error in get_analyzed_repos: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing repository data: {e}")
            return []

    def persist_flow_state(self, state: FlowState) -> bool:
        """Persist flow state to database.
        
        Args:
            state (FlowState): Current flow state to persist
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Persisting flow state")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Start transaction
                cursor.execute("BEGIN TRANSACTION")
                
                try:
                    # Set all existing states to not latest
                    cursor.execute("""
                        UPDATE flow_state
                        SET is_latest = FALSE
                        WHERE is_latest = TRUE
                    """)
                    
                    # Insert new state
                    state_json = json.dumps(state.dict(), cls=DateTimeEncoder)
                    cursor.execute("""
                        INSERT INTO flow_state (state_data, is_latest)
                        VALUES (?, TRUE)
                    """, (state_json,))
                    
                    # Commit transaction
                    conn.commit()
                    logger.info("Flow state persisted successfully")
                    return True
                    
                except Exception as e:
                    # Rollback on error
                    conn.rollback()
                    logger.error(f"Error in persist_flow_state transaction: {e}")
                    return False
                
        except sqlite3.Error as e:
            logger.error(f"Database error in persist_flow_state: {e}")
            return False

    def load_flow_state(self) -> Optional[FlowState]:
        """Load latest flow state from database.
        
        Returns:
            Optional[FlowState]: Latest flow state or None if not found
        """
        logger.info("Loading latest flow state")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get latest state
                cursor.execute("""
                    SELECT state_data
                    FROM flow_state
                    WHERE is_latest = TRUE
                    ORDER BY created_at DESC
                    LIMIT 1
                """)
                
                result = cursor.fetchone()
                if result:
                    state_dict = json.loads(result[0])
                    logger.info("Successfully loaded flow state")
                    return FlowState.parse_obj(state_dict)
                else:
                    logger.info("No existing flow state found")
                    return None
                    
        except sqlite3.Error as e:
            logger.error(f"Database error in load_flow_state: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing flow state: {e}")
            return None

    def cleanup_flow_states(self, keep_latest: int = 5):
        """Clean up old flow states, keeping only the specified number of latest states.
        
        Args:
            keep_latest (int): Number of latest states to keep
        """
        logger.info(f"Cleaning up flow states, keeping {keep_latest} latest")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Start transaction
                cursor.execute("BEGIN TRANSACTION")
                
                try:
                    # Get IDs of states to keep
                    cursor.execute("""
                        SELECT id FROM flow_state
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (keep_latest,))
                    
                    keep_ids = [row[0] for row in cursor.fetchall()]
                    
                    if keep_ids:
                        # Delete all states except those in keep_ids
                        cursor.execute("""
                            DELETE FROM flow_state
                            WHERE id NOT IN ({})
                        """.format(','.join('?' * len(keep_ids))), keep_ids)
                    
                    # Commit transaction
                    conn.commit()
                    logger.info(f"Successfully cleaned up flow states, kept {len(keep_ids)} latest")
                    
                except Exception as e:
                    # Rollback on error
                    conn.rollback()
                    logger.error(f"Error in cleanup_flow_states transaction: {e}")
                
        except sqlite3.Error as e:
            logger.error(f"Database error in cleanup_flow_states: {e}")

    def store_raw_repos(self, repos: List[Dict], source: str, batch_id: Optional[int] = None) -> bool:
        """Store raw repository data in the database.
        
        Args:
            repos (List[Dict]): List of repository data to store
            source (str): Source of the repositories (e.g., 'starred', 'trending')
            batch_id (Optional[int]): Batch ID for processing tracking
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Storing {len(repos)} repositories from source: {source}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Start transaction
                cursor.execute("BEGIN TRANSACTION")
                
                try:
                    # Insert repos
                    for repo in repos:
                        repo_json = json.dumps(repo, cls=DateTimeEncoder)
                        cursor.execute("""
                            INSERT INTO raw_repositories (source, data, batch_id)
                            VALUES (?, ?, ?)
                        """, (source, repo_json, batch_id))
                    
                    # Commit transaction
                    conn.commit()
                    logger.info(f"Successfully stored {len(repos)} repositories")
                    return True
                    
                except Exception as e:
                    # Rollback on error
                    conn.rollback()
                    logger.error(f"Error in store_raw_repos transaction: {e}")
                    return False
                
        except sqlite3.Error as e:
            logger.error(f"Database error in store_raw_repos: {e}")
            return False

    def store_analyzed_repos(self, analyzed_repos: List[Dict], batch_id: Optional[int] = None) -> bool:
        """Store analyzed repository data in the database.
        
        Args:
            analyzed_repos (List[Dict]): List of analyzed repository data
            batch_id (Optional[int]): Batch ID for processing tracking
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Storing {len(analyzed_repos)} analyzed repositories")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Start transaction
                cursor.execute("BEGIN TRANSACTION")
                
                try:
                    # Insert analyzed repos
                    for repo in analyzed_repos:
                        # Get raw repo ID
                        cursor.execute("""
                            SELECT id FROM raw_repositories
                            WHERE data->>'$.full_name' = ?
                        """, (repo['full_name'],))
                        
                        raw_repo_id = cursor.fetchone()
                        if raw_repo_id:
                            analysis_json = json.dumps({
                                'quality_score': repo.get('quality_score'),
                                'category': repo.get('category'),
                                'subcategory': repo.get('subcategory'),
                                'include': repo.get('include', True),
                                'justification': repo.get('justification'),
                                'key_features': repo.get('key_features', [])
                            }, cls=DateTimeEncoder)
                            
                            cursor.execute("""
                                INSERT INTO analyzed_repositories 
                                (raw_repo_id, analysis_data, batch_id)
                                VALUES (?, ?, ?)
                            """, (raw_repo_id[0], analysis_json, batch_id))
                            
                            # Mark raw repo as processed
                            cursor.execute("""
                                UPDATE raw_repositories
                                SET processed = TRUE
                                WHERE id = ?
                            """, (raw_repo_id[0],))
                    
                    # Commit transaction
                    conn.commit()
                    logger.info(f"Successfully stored {len(analyzed_repos)} analyzed repositories")
                    return True
                    
                except Exception as e:
                    # Rollback on error
                    conn.rollback()
                    logger.error(f"Error in store_analyzed_repos transaction: {e}")
                    return False
                
        except sqlite3.Error as e:
            logger.error(f"Database error in store_analyzed_repos: {e}")
            return False
