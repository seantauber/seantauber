"""Database migration management."""

import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

# List of migrations as tuples of (version, up_sql, down_sql)
MIGRATIONS: List[Tuple[int, str, str]] = [
    (
        1,
        # Up migration
        """
        CREATE TABLE IF NOT EXISTS newsletters (
            id INTEGER PRIMARY KEY,
            email_id TEXT NOT NULL UNIQUE,
            received_date TIMESTAMP NOT NULL,
            processed_date TIMESTAMP,
            storage_status TEXT NOT NULL, -- 'active', 'archived', 'summarized'
            vector_id TEXT,              -- Reference to vector storage
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_newsletters_email_id ON newsletters(email_id);
        CREATE INDEX IF NOT EXISTS idx_newsletters_received_date ON newsletters(received_date);
        CREATE INDEX IF NOT EXISTS idx_newsletters_processed_date ON newsletters(processed_date);
        """,
        # Down migration
        """
        DROP TABLE IF EXISTS newsletters;
        """
    ),
    (
        2,
        # Up migration
        """
        CREATE TABLE IF NOT EXISTS content_extraction_status (
            id INTEGER PRIMARY KEY,
            vector_id TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,  -- 'pending', 'processing', 'completed', 'failed'
            attempt_count INTEGER DEFAULT 0,
            last_attempt TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_extraction_vector_id ON content_extraction_status(vector_id);
        CREATE INDEX IF NOT EXISTS idx_extraction_status ON content_extraction_status(status);
        
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY,
            key TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Trigger to update timestamps
        CREATE TRIGGER IF NOT EXISTS update_extraction_timestamp 
        AFTER UPDATE ON content_extraction_status
        BEGIN
            UPDATE content_extraction_status 
            SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = NEW.id;
        END;
        """,
        # Down migration
        """
        DROP TABLE IF EXISTS content_extraction_status;
        DROP TABLE IF EXISTS system_config;
        """
    )
]

def get_current_version(cursor) -> int:
    """Get the current database version."""
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
            """
        )
        cursor.execute("SELECT version FROM schema_version")
        result = cursor.fetchone()
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Failed to get schema version: {str(e)}")
        return 0

def set_version(cursor, version: int) -> None:
    """Set the current database version."""
    try:
        cursor.execute("DELETE FROM schema_version")
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
    except Exception as e:
        logger.error(f"Failed to set schema version: {str(e)}")
        raise

def migrate(cursor, target_version: Optional[int] = None) -> None:
    """
    Run database migrations.
    
    Args:
        cursor: Database cursor
        target_version: Optional specific version to migrate to
    """
    current = get_current_version(cursor)
    if target_version is None:
        target_version = len(MIGRATIONS)
    
    logger.info(f"Current database version: {current}")
    logger.info(f"Target database version: {target_version}")
    
    if current == target_version:
        logger.info("Database is up to date")
        return
        
    try:
        # Migrate up
        if target_version > current:
            for version, up_sql, _ in MIGRATIONS[current:target_version]:
                logger.info(f"Running migration {version} (up)")
                cursor.executescript(up_sql)
                set_version(cursor, version)
                logger.info(f"Completed migration {version}")
        
        # Migrate down
        else:
            for version, _, down_sql in reversed(MIGRATIONS[target_version:current]):
                logger.info(f"Running migration {version} (down)")
                cursor.executescript(down_sql)
                set_version(cursor, version - 1)
                logger.info(f"Completed migration {version}")
        
        logger.info(f"Database migrated successfully to version {target_version}")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise
