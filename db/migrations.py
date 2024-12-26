"""Database migration management."""

import logging
from typing import List, Optional
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class Migration(ABC):
    """Base class for database migrations."""
    
    @abstractmethod
    def upgrade(self, db) -> None:
        """Apply the migration."""
        pass
    
    @abstractmethod
    def downgrade(self, db) -> None:
        """Revert the migration."""
        pass

class InitialMigration(Migration):
    """Initial database migration that sets up all required tables."""
    
    def upgrade(self, db) -> None:
        """Create all initial tables."""
        db.executescript("""
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS newsletters (
            id INTEGER PRIMARY KEY,
            email_id TEXT NOT NULL UNIQUE,
            received_date TIMESTAMP NOT NULL,
            processed_date TIMESTAMP,
            storage_status TEXT NOT NULL,
            vector_id TEXT,
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY,
            key TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS agent_operations (
            id INTEGER PRIMARY KEY,
            agent_name TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT
        );
        
        CREATE TABLE IF NOT EXISTS repositories (
            id INTEGER PRIMARY KEY,
            github_url TEXT NOT NULL UNIQUE,
            first_seen_date TIMESTAMP NOT NULL,
            last_mentioned_date TIMESTAMP NOT NULL,
            metadata JSON
        );
        
        CREATE TABLE IF NOT EXISTS content_cache (
            id INTEGER PRIMARY KEY,
            url TEXT NOT NULL UNIQUE,
            content_type TEXT NOT NULL,
            content BLOB NOT NULL,
            last_accessed TIMESTAMP NOT NULL,
            expires_at TIMESTAMP NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS active_storage_rules (
            id INTEGER PRIMARY KEY,
            pattern TEXT NOT NULL UNIQUE,
            priority INTEGER NOT NULL,
            action TEXT NOT NULL,
            conditions JSON
        );
        
        CREATE TABLE IF NOT EXISTS archive_storage_rules (
            id INTEGER PRIMARY KEY,
            pattern TEXT NOT NULL UNIQUE,
            priority INTEGER NOT NULL,
            action TEXT NOT NULL,
            conditions JSON
        );
        
        CREATE TABLE IF NOT EXISTS permanent_storage_rules (
            id INTEGER PRIMARY KEY,
            pattern TEXT NOT NULL UNIQUE,
            priority INTEGER NOT NULL,
            action TEXT NOT NULL,
            conditions JSON
        );
        
        CREATE TABLE IF NOT EXISTS archival_jobs (
            id INTEGER PRIMARY KEY,
            content_id TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT
        );
        
        CREATE TABLE IF NOT EXISTS retention_triggers (
            id INTEGER PRIMARY KEY,
            content_id TEXT NOT NULL,
            trigger_type TEXT NOT NULL,
            trigger_date TIMESTAMP NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS content_summaries (
            id INTEGER PRIMARY KEY,
            content_id TEXT NOT NULL UNIQUE,
            summary TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_newsletters_email_id ON newsletters(email_id);
        CREATE INDEX IF NOT EXISTS idx_newsletters_received_date ON newsletters(received_date);
        CREATE INDEX IF NOT EXISTS idx_newsletters_processed_date ON newsletters(processed_date);
        """)
    
    def downgrade(self, db) -> None:
        """Remove all tables."""
        db.executescript("""
        DROP TABLE IF EXISTS migrations;
        DROP TABLE IF EXISTS newsletters;
        DROP TABLE IF EXISTS system_config;
        DROP TABLE IF EXISTS agent_operations;
        DROP TABLE IF EXISTS repositories;
        DROP TABLE IF EXISTS content_cache;
        DROP TABLE IF EXISTS active_storage_rules;
        DROP TABLE IF EXISTS archive_storage_rules;
        DROP TABLE IF EXISTS permanent_storage_rules;
        DROP TABLE IF EXISTS archival_jobs;
        DROP TABLE IF EXISTS retention_triggers;
        DROP TABLE IF EXISTS content_summaries;
        """)

class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, db):
        """Initialize with database connection."""
        self.db = db
        self._migrations: List[Migration] = [InitialMigration()]
    
    def _get_applied_migrations(self) -> List[str]:
        """Get list of applied migration names."""
        try:
            return [
                row["name"] for row in 
                self.db.fetch_all("SELECT name FROM migrations ORDER BY id")
            ]
        except Exception:
            return []
    
    def apply_migrations(self) -> None:
        """Apply all pending migrations."""
        applied = self._get_applied_migrations()
        
        for migration in self._migrations:
            name = migration.__class__.__name__
            if name not in applied:
                logger.info(f"Applying migration: {name}")
                try:
                    migration.upgrade(self.db)
                    self.db.execute(
                        "INSERT INTO migrations (name) VALUES (?)",
                        (name,)
                    )
                    logger.info(f"Successfully applied migration: {name}")
                except Exception as e:
                    logger.error(f"Failed to apply migration {name}: {str(e)}")
                    raise
    
    def revert_migrations(self) -> None:
        """Revert all migrations in reverse order."""
        applied = self._get_applied_migrations()
        
        for migration in reversed(self._migrations):
            name = migration.__class__.__name__
            if name in applied:
                logger.info(f"Reverting migration: {name}")
                try:
                    migration.downgrade(self.db)
                    self.db.execute(
                        "DELETE FROM migrations WHERE name = ?",
                        (name,)
                    )
                    logger.info(f"Successfully reverted migration: {name}")
                except Exception as e:
                    logger.error(f"Failed to revert migration {name}: {str(e)}")
                    raise
