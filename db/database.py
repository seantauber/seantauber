import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from models.github_repo_data import GitHubRepoData, AnalyzedRepoData, CombinedRepoData

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

    # Rest of the class implementation remains exactly the same...
    def verify_state(self) -> Dict:
        """Verify database state and table contents.
        
        Returns:
            Dict: Current state of the database including table counts and status
        """
        logger.info("Verifying database state")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check table existence
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ('raw_repositories', 'analyzed_repositories', 'batch_processing')
                """)
                existing_tables = [row[0] for row in cursor.fetchall()]
                logger.debug(f"Existing tables: {existing_tables}")
                
                state = {
                    'tables_exist': {
                        'raw_repositories': 'raw_repositories' in existing_tables,
                        'analyzed_repositories': 'analyzed_repositories' in existing_tables,
                        'batch_processing': 'batch_processing' in existing_tables
                    },
                    'row_counts': {},
                    'last_operation': self._state['last_operation'],
                    'last_operation_time': self._state['last_operation_time'],
                    'connection_active': self._state['connection_active']
                }
                
                # Get row counts for each table
                for table in existing_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    state['row_counts'][table] = cursor.fetchone()[0]
                
                logger.info(f"Database state verified: {state}")
                return state
                
        except sqlite3.Error as e:
            logger.error(f"Error verifying database state: {e}")
            self._state['connection_active'] = False
            raise

    def _update_state(self, operation: str):
        """Update the internal state tracking.
        
        Args:
            operation (str): Name of the operation being performed
        """
        self._state['last_operation'] = operation
        self._state['last_operation_time'] = datetime.now().isoformat()
        self._state['connection_active'] = True
        logger.debug(f"Updated state: {operation}")
    
    def cleanup_database(self):
        """Clear all data from the database tables."""
        logger.info("Starting database cleanup")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get counts before cleanup
                cursor.execute("SELECT COUNT(*) FROM analyzed_repositories")
                analyzed_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM raw_repositories")
                raw_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM batch_processing")
                batch_count = cursor.fetchone()[0]
                
                logger.info(f"Current table counts - Analyzed: {analyzed_count}, Raw: {raw_count}, Batch: {batch_count}")
                logger.debug("Starting transaction for database cleanup")
                
                # Delete all data from tables in correct order to maintain foreign key constraints
                cursor.execute("DELETE FROM analyzed_repositories")
                logger.debug("Deleted all records from analyzed_repositories")
                cursor.execute("DELETE FROM raw_repositories")
                logger.debug("Deleted all records from raw_repositories")
                cursor.execute("DELETE FROM batch_processing")
                logger.debug("Deleted all records from batch_processing")
                
                # Try to reset auto-increment counters
                try:
                    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('analyzed_repositories', 'raw_repositories', 'batch_processing')")
                    logger.debug("Reset auto-increment counters")
                except sqlite3.OperationalError as e:
                    if "no such table: sqlite_sequence" in str(e):
                        logger.info("sqlite_sequence table does not exist yet - skipping cleanup")
                    else:
                        raise
                
                conn.commit()
                logger.debug("Cleanup transaction committed successfully")
                logger.info("Database cleaned up successfully")
                
                self._update_state('cleanup_database')
                
        except sqlite3.Error as e:
            logger.error(f"Error cleaning up database: {e}")
            self._state['connection_active'] = False
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
                
                conn.commit()
                logger.debug("Database initialization transaction committed successfully")
                logger.info("Database initialized successfully")
                
                self._state['tables_initialized'] = True
                self._update_state('init_db')
                
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            self._state['connection_active'] = False
            raise
    
    def store_raw_repos(self, repos: List[GitHubRepoData], source: str, batch_id: Optional[int] = None):
        """Store raw repository data in the database with enhanced transaction logging.
        
        Args:
            repos (List[GitHubRepoData]): List of GitHubRepoData objects
            source (str): Source of the repositories ('starred' or 'trending')
            batch_id (Optional[int]): ID of the processing batch
        """
        logger.info(f"Starting store_raw_repos operation for {len(repos)} repositories from source: {source}")
        logger.debug(f"Batch ID: {batch_id}, Source: {source}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                stored_count = 0
                error_count = 0
                
                for repo in repos:
                    try:
                        # Log each repository being processed
                        logger.debug(f"Processing repository: {repo.full_name}")
                        logger.debug(f"Repository details - Stars: {repo.stargazers_count}, Language: {repo.language}")
                        
                        # Convert GitHubRepoData to dict and then to JSON using custom encoder
                        repo_dict = repo.dict()
                        json_data = json.dumps(repo_dict, cls=DateTimeEncoder)
                        
                        # Verify JSON data
                        try:
                            parsed_data = json.loads(json_data)  # Validate JSON
                            logger.debug(f"Valid JSON data for repository: {repo.full_name}")
                            logger.debug(f"JSON data size: {len(json_data)} bytes")
                            logger.debug(f"Parsed data contains {len(parsed_data)} fields")
                        except json.JSONDecodeError as je:
                            logger.error(f"Invalid JSON data for repository {repo.full_name}: {je}")
                            error_count += 1
                            continue
                        
                        # Insert repository data
                        cursor.execute(
                            """
                            INSERT INTO raw_repositories (source, data, batch_id)
                            VALUES (?, ?, ?)
                            """,
                            (source, json_data, batch_id)
                        )
                        stored_count += 1
                        logger.debug(f"Successfully stored repository: {repo.full_name} with row id: {cursor.lastrowid}")
                        
                    except Exception as e:
                        logger.error(f"Error processing repository {repo.full_name}: {e}")
                        error_count += 1
                        continue
                
                conn.commit()
                logger.debug("Transaction committed successfully")
                logger.info(f"Transaction completed - Stored: {stored_count}, Errors: {error_count}")
                
                # Verify stored data
                cursor.execute("SELECT COUNT(*) FROM raw_repositories WHERE batch_id = ?", (batch_id,))
                verified_count = cursor.fetchone()[0]
                logger.debug(f"Running verification query for batch {batch_id}")
                logger.info(f"Verified {verified_count} repositories stored in batch {batch_id}")
                
                self._update_state('store_raw_repos')
                
        except sqlite3.Error as e:
            logger.error(f"Database error in store_raw_repos: {e}")
            self._state['connection_active'] = False
            raise
        except Exception as e:
            logger.error(f"Unexpected error in store_raw_repos: {e}")
            raise
    
    def get_unprocessed_repos(self, batch_size: int = 10) -> List[Dict]:
        """Retrieve a batch of unprocessed repositories.
        
        Args:
            batch_size (int): Number of repositories to retrieve
            
        Returns:
            List[Dict]: List of unprocessed repository data
        """
        logger.info(f"Retrieving {batch_size} unprocessed repositories")
        logger.debug(f"Executing get_unprocessed_repos with batch_size: {batch_size}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # First, check total unprocessed count
                cursor.execute("SELECT COUNT(*) FROM raw_repositories WHERE processed = FALSE")
                total_unprocessed = cursor.fetchone()[0]
                logger.debug(f"Total unprocessed repositories in database: {total_unprocessed}")
                
                # Get the batch of unprocessed repos
                cursor.execute(
                    """
                    SELECT id, source, data FROM raw_repositories
                    WHERE processed = FALSE
                    LIMIT ?
                    """,
                    (batch_size,)
                )
                results = cursor.fetchall()
                logger.debug(f"Retrieved {len(results)} rows from database")
                
                repos = []
                for row in results:
                    try:
                        repo_id = row[0]
                        source = row[1]
                        logger.debug(f"Processing row id: {repo_id}, source: {source}")
                        
                        # Parse JSON data
                        repo_data = json.loads(row[2])
                        logger.debug(f"Successfully parsed JSON data for repo id: {repo_id}")
                        
                        repo_data['source'] = source  # Add source to the data
                        repos.append({
                            'id': repo_id,
                            'data': repo_data
                        })
                        logger.debug(f"Added repository {repo_id} to result set")
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding JSON for repository {row[0]}: {e}")
                        continue
                    
                logger.info(f"Retrieved {len(repos)} unprocessed repositories")
                logger.debug(f"Remaining unprocessed: {total_unprocessed - len(repos)}")
                
                self._update_state('get_unprocessed_repos')
                return repos
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving unprocessed repositories: {e}")
            self._state['connection_active'] = False
            raise
    
    def store_analyzed_repos(self, analyzed_repos: List[Dict], batch_id: Optional[int] = None):
        """Store analyzed repository data and mark raw repos as processed.
        
        Args:
            analyzed_repos (List[Dict]): List of analyzed repository data
            batch_id (Optional[int]): ID of the processing batch
        """
        logger.info(f"Starting store_analyzed_repos operation for batch {batch_id}")
        logger.debug(f"Processing {len(analyzed_repos)} analyzed repositories")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                stored_count = 0
                error_count = 0
                
                for repo in analyzed_repos:
                    try:
                        # Extract required fields
                        raw_repo_id = repo.get('raw_repo_id')
                        if not raw_repo_id:
                            logger.error(f"Missing raw_repo_id in analyzed repo data: {repo}")
                            error_count += 1
                            continue

                        logger.debug(f"Processing analyzed data for raw_repo_id: {raw_repo_id}")

                        # Create analysis data structure
                        analysis_data = {
                            'quality_score': repo.get('quality_score', 0.0),
                            'category': repo.get('category', ''),
                            'subcategory': repo.get('subcategory', ''),
                            'include': repo.get('include', True),
                            'justification': repo.get('justification', '')
                        }
                        
                        logger.debug(f"Analysis data for repo {raw_repo_id}: {json.dumps(analysis_data)}")

                        # Store analyzed data
                        cursor.execute(
                            """
                            INSERT INTO analyzed_repositories (
                                raw_repo_id, analysis_data, batch_id
                            )
                            VALUES (?, ?, ?)
                            """,
                            (
                                raw_repo_id,
                                json.dumps(analysis_data, cls=DateTimeEncoder),
                                batch_id
                            )
                        )
                        analyzed_id = cursor.lastrowid
                        logger.debug(f"Inserted analyzed data with id: {analyzed_id}")
                        
                        # Mark raw repo as processed
                        cursor.execute(
                            """
                            UPDATE raw_repositories
                            SET processed = TRUE
                            WHERE id = ?
                            """,
                            (raw_repo_id,)
                        )
                        stored_count += 1
                        logger.debug(f"Successfully stored and marked as processed: raw_repo_id {raw_repo_id}")
                        
                    except Exception as e:
                        logger.error(f"Error processing analyzed repo with raw_repo_id {raw_repo_id}: {e}")
                        error_count += 1
                        continue
                
                conn.commit()
                logger.debug("Transaction committed successfully")
                logger.info(f"Transaction completed - Stored: {stored_count}, Errors: {error_count}")
                
                # Verify the updates
                cursor.execute("SELECT COUNT(*) FROM analyzed_repositories WHERE batch_id = ?", (batch_id,))
                verified_count = cursor.fetchone()[0]
                logger.debug(f"Verification: {verified_count} analyzed repositories in batch {batch_id}")
                
                self._update_state('store_analyzed_repos')
                
        except sqlite3.Error as e:
            logger.error(f"Database error in store_analyzed_repos: {e}")
            self._state['connection_active'] = False
            raise
        except Exception as e:
            logger.error(f"Unexpected error in store_analyzed_repos: {e}")
            raise
    
    def get_analyzed_repos(self) -> List[Dict]:
        """Retrieve all analyzed repositories.
        
        Returns:
            List[Dict]: List of analyzed repository data
        """
        logger.info("Retrieving all analyzed repositories")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # First, get count of analyzed repos
                cursor.execute("SELECT COUNT(*) FROM analyzed_repositories")
                total_count = cursor.fetchone()[0]
                logger.debug(f"Total analyzed repositories in database: {total_count}")
                
                # Get all analyzed repositories with their raw data
                query = """
                    SELECT 
                        r.source,
                        r.data as raw_data,
                        a.analysis_data,
                        json_extract(a.analysis_data, '$.quality_score') as quality_score,
                        json_extract(a.analysis_data, '$.category') as category,
                        json_extract(a.analysis_data, '$.subcategory') as subcategory,
                        json_extract(a.analysis_data, '$.include') as include,
                        json_extract(a.analysis_data, '$.justification') as justification,
                        r.id as raw_id,
                        a.id as analyzed_id
                    FROM analyzed_repositories a
                    JOIN raw_repositories r ON r.id = a.raw_repo_id
                    WHERE json_extract(a.analysis_data, '$.include') = TRUE
                    ORDER BY json_extract(a.analysis_data, '$.quality_score') DESC, r.created_at DESC
                """
                logger.debug("Executing analyzed repositories query")
                cursor.execute(query)
                
                results = cursor.fetchall()
                logger.debug(f"Retrieved {len(results)} rows from database")
                
                if not results:
                    logger.warning("No analyzed repositories found in database")
                    return []
                
                analyzed_repos = []
                for row in results:
                    try:
                        raw_id = row[8]
                        analyzed_id = row[9]
                        logger.debug(f"Processing row - Raw ID: {raw_id}, Analyzed ID: {analyzed_id}")
                        
                        raw_data = json.loads(row[1])
                        analysis_data = json.loads(row[2])
                        logger.debug(f"Successfully parsed JSON data for repo {raw_id}")
                        
                        analyzed_repos.append({
                            'source': row[0],
                            'repo_data': raw_data,
                            'analysis_data': analysis_data,
                            'quality_score': row[3],
                            'category': row[4],
                            'subcategory': row[5],
                            'include': row[6],
                            'justification': row[7],
                            'raw_id': raw_id,
                            'analyzed_id': analyzed_id
                        })
                        logger.debug(f"Added analyzed repository {raw_id} to result set")
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding JSON for repository {row[8]}: {e}")
                        continue
                
                logger.info(f"Retrieved {len(analyzed_repos)} analyzed repositories successfully")
                logger.debug("Analyzed repositories retrieval completed")
                
                self._update_state('get_analyzed_repos')
                return analyzed_repos
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving analyzed repositories: {e}")
            self._state['connection_active'] = False
            raise

    def create_batch(self, task_type: str) -> int:
        """Create a new batch processing record.
        
        Args:
            task_type (str): Type of task ('fetch', 'analyze', etc.)
            
        Returns:
            int: ID of the created batch
        """
        logger.info(f"Creating new batch for task type: {task_type}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current max batch_id
                cursor.execute(
                    "SELECT MAX(batch_id) FROM batch_processing WHERE task_type = ?",
                    (task_type,)
                )
                current_max = cursor.fetchone()[0]
                new_batch_id = (current_max or 0) + 1
                logger.debug(f"Calculated new batch_id: {new_batch_id}")
                
                cursor.execute(
                    """
                    INSERT INTO batch_processing (task_type, batch_id, status, started_at)
                    VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
                    """,
                    (task_type, new_batch_id)
                )
                batch_id = cursor.lastrowid
                logger.debug(f"Inserted new batch with ID: {batch_id}")
                
                conn.commit()
                logger.info(f"Created new batch {batch_id} for task type {task_type}")
                
                self._update_state('create_batch')
                return batch_id
                
        except sqlite3.Error as e:
            logger.error(f"Error creating batch: {e}")
            self._state['connection_active'] = False
            raise

    def update_batch_status(self, batch_id: int, status: str, error: Optional[str] = None):
        """Update the status of a batch processing record.
        
        Args:
            batch_id (int): ID of the batch to update
            status (str): New status ('pending', 'processing', 'completed', 'failed', 'retry_queue', 'cleaned_up')
            error (Optional[str]): Error message if status is 'failed'
        """
        logger.info(f"Updating batch {batch_id} status to: {status}")
        logger.debug(f"Batch update details - ID: {batch_id}, Status: {status}, Error: {error}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current status
                cursor.execute(
                    "SELECT status FROM batch_processing WHERE id = ?",
                    (batch_id,)
                )
                current_status = cursor.fetchone()
                logger.debug(f"Current batch status: {current_status[0] if current_status else 'Not found'}")
                
                if status in ('completed', 'failed', 'cleaned_up'):
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
                logger.debug("Batch status update committed successfully")
                logger.info(f"Successfully updated batch {batch_id} status to {status}")
                
                self._update_state('update_batch_status')
                
        except sqlite3.Error as e:
            logger.error(f"Error updating batch status: {e}")
            self._state['connection_active'] = False
            raise

    def get_batch_status(self, task_type: str) -> Dict[int, Dict]:
        """Get status of all batches for a task type.
        
        Args:
            task_type (str): Type of task to get status for
            
        Returns:
            Dict[int, Dict]: Dictionary of batch IDs to their status information
        """
        logger.info(f"Getting batch status for task type: {task_type}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get count of batches
                cursor.execute(
                    "SELECT COUNT(*) FROM batch_processing WHERE task_type = ?",
                    (task_type,)
                )
                total_batches = cursor.fetchone()[0]
                logger.debug(f"Total batches for task type {task_type}: {total_batches}")
                
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
                
                status_dict = {}
                for row in results:
                    batch_id = row[0]
                    status = row[1]
                    logger.debug(f"Processing batch {batch_id} with status: {status}")
                    
                    status_dict[batch_id] = {
                        'status': status,
                        'started_at': row[2],
                        'completed_at': row[3],
                        'error': row[4]
                    }
                
                logger.info(f"Retrieved status for {len(status_dict)} batches of type {task_type}")
                logger.debug(f"Status distribution: {[status['status'] for status in status_dict.values()]}")
                
                self._update_state('get_batch_status')
                return status_dict
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving batch status: {e}")
            self._state['connection_active'] = False
            raise
