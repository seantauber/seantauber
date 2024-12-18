"""Database migration management module."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Any
import importlib.util
import os
from pathlib import Path

from db.connection import Database, DatabaseError

logger = logging.getLogger(__name__)

class Migration(ABC):
    """Abstract base class for database migrations."""
    
    @abstractmethod
    def upgrade(self, db: Database) -> None:
        """Apply migration changes.
        
        Args:
            db: Database instance.
            
        Raises:
            DatabaseError: If migration fails.
        """
        pass
    
    @abstractmethod
    def downgrade(self, db: Database) -> None:
        """Revert migration changes.
        
        Args:
            db: Database instance.
            
        Raises:
            DatabaseError: If migration reversion fails.
        """
        pass

class InitialMigration(Migration):
    """Initial database migration creating core tables."""
    
    def upgrade(self, db: Database) -> None:
        """Create core database tables.
        
        Args:
            db: Database instance.
            
        Raises:
            DatabaseError: If table creation fails.
        """
        try:
            # Create migrations table first
            db.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    applied_at TIMESTAMP NOT NULL
                )
            """)
            
            # Create system_config table
            db.execute("""
                CREATE TABLE system_config (
                    id INTEGER PRIMARY KEY,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create agent_operations table
            db.execute("""
                CREATE TABLE agent_operations (
                    id INTEGER PRIMARY KEY,
                    agent_type TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    metadata JSON
                )
            """)
            
            # Create newsletters table
            db.execute("""
                CREATE TABLE newsletters (
                    id INTEGER PRIMARY KEY,
                    email_id TEXT NOT NULL UNIQUE,
                    received_date TIMESTAMP NOT NULL,
                    processed_date TIMESTAMP,
                    storage_status TEXT NOT NULL,
                    vector_id TEXT,
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create repositories table
            db.execute("""
                CREATE TABLE repositories (
                    id INTEGER PRIMARY KEY,
                    github_url TEXT NOT NULL UNIQUE,
                    first_seen_date TIMESTAMP NOT NULL,
                    last_mentioned_date TIMESTAMP NOT NULL,
                    mention_count INTEGER DEFAULT 1,
                    vector_id TEXT,
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create content_cache table
            db.execute("""
                CREATE TABLE content_cache (
                    id INTEGER PRIMARY KEY,
                    url TEXT NOT NULL UNIQUE,
                    content_type TEXT NOT NULL,
                    content BLOB,
                    last_accessed TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create active_storage_rules table
            db.execute("""
                CREATE TABLE active_storage_rules (
                    id INTEGER PRIMARY KEY,
                    content_type TEXT NOT NULL,
                    retention_period_days INTEGER NOT NULL,
                    archival_policy TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create archive_storage_rules table
            db.execute("""
                CREATE TABLE archive_storage_rules (
                    id INTEGER PRIMARY KEY,
                    content_type TEXT NOT NULL,
                    retention_period_days INTEGER NOT NULL,
                    summarization_policy TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create permanent_storage_rules table
            db.execute("""
                CREATE TABLE permanent_storage_rules (
                    id INTEGER PRIMARY KEY,
                    content_type TEXT NOT NULL,
                    criteria JSON NOT NULL,
                    storage_policy TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create archival_jobs table
            db.execute("""
                CREATE TABLE archival_jobs (
                    id INTEGER PRIMARY KEY,
                    content_type TEXT NOT NULL,
                    source_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    summary_vector_id TEXT,
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create retention_triggers table
            db.execute("""
                CREATE TABLE retention_triggers (
                    id INTEGER PRIMARY KEY,
                    trigger_type TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    condition_sql TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create content_summaries table
            db.execute("""
                CREATE TABLE content_summaries (
                    id INTEGER PRIMARY KEY,
                    original_content_id INTEGER NOT NULL,
                    content_type TEXT NOT NULL,
                    summary_type TEXT NOT NULL,
                    vector_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSON
                )
            """)

        except DatabaseError as e:
            raise DatabaseError(f"Failed to create tables: {str(e)}")
    
    def downgrade(self, db: Database) -> None:
        """Remove core database tables.
        
        Args:
            db: Database instance.
            
        Raises:
            DatabaseError: If table removal fails.
        """
        try:
            # Drop tables in reverse order of creation
            tables = [
                "content_summaries",
                "retention_triggers",
                "archival_jobs",
                "permanent_storage_rules",
                "archive_storage_rules",
                "active_storage_rules",
                "content_cache",
                "repositories",
                "newsletters",
                "agent_operations",
                "system_config",
                "migrations"
            ]
            
            for table in tables:
                db.execute(f"DROP TABLE IF EXISTS {table}")
        except DatabaseError as e:
            raise DatabaseError(f"Failed to remove tables: {str(e)}")

class MigrationWrapper(Migration):
    """Wrapper for migration modules."""
    
    def __init__(self, name: str, module: Any) -> None:
        """Initialize migration wrapper.
        
        Args:
            name: Migration name
            module: Migration module
        """
        self.name = name
        self.module = module
    
    def upgrade(self, db: Database) -> None:
        """Apply migration changes."""
        self.module.upgrade(db)
    
    def downgrade(self, db: Database) -> None:
        """Revert migration changes."""
        self.module.downgrade(db)

class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, db: Database) -> None:
        """Initialize migration manager.
        
        Args:
            db: Database instance.
        """
        self.db = db
        self._migrations: List[Migration] = self._load_migrations()
    
    def _load_migrations(self) -> List[Migration]:
        """Load all migrations in order.
        
        Returns:
            List of migrations.
        """
        migrations = [InitialMigration()]
        
        # Get migration files
        migration_dir = Path(__file__).parent / "migrations"
        if not migration_dir.exists():
            return migrations
            
        migration_files = sorted([
            f for f in migration_dir.glob("*.py")
            if f.name.startswith("0")
        ])
        
        # Load each migration module
        for file_path in migration_files:
            name = file_path.stem
            spec = importlib.util.spec_from_file_location(name, file_path)
            if spec is None or spec.loader is None:
                continue
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            migrations.append(MigrationWrapper(name, module))
        
        return migrations
    
    def _migrations_table_exists(self) -> bool:
        """Check if migrations table exists.
        
        Returns:
            True if migrations table exists, False otherwise.
        """
        try:
            result = self.db.fetch_one("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='migrations'
            """)
            return result is not None
        except DatabaseError:
            return False
    
    def _get_applied_migrations(self) -> List[str]:
        """Get list of applied migration names.
        
        Returns:
            List of applied migration names.
        """
        if not self._migrations_table_exists():
            return []
            
        try:
            rows = self.db.fetch_all(
                "SELECT name FROM migrations ORDER BY applied_at"
            )
            return [row['name'] for row in rows]
        except DatabaseError:
            return []
    
    def _record_migration(self, name: str) -> None:
        """Record that a migration has been applied.
        
        Args:
            name: Migration name.
            
        Raises:
            DatabaseError: If recording fails.
        """
        try:
            # Create migrations table if it doesn't exist
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    applied_at TIMESTAMP NOT NULL
                )
            """)
            
            self.db.execute(
                "INSERT INTO migrations (name, applied_at) VALUES (?, ?)",
                (name, datetime.utcnow().isoformat())
            )
        except DatabaseError as e:
            raise DatabaseError(f"Failed to record migration {name}: {str(e)}")
    
    def _remove_migration_record(self, name: str) -> None:
        """Remove migration record.
        
        Args:
            name: Migration name.
        """
        if not self._migrations_table_exists():
            return
            
        try:
            self.db.execute(
                "DELETE FROM migrations WHERE name = ?",
                (name,)
            )
        except DatabaseError:
            # Ignore errors when removing migration records during reversion
            pass
    
    def apply_migrations(self) -> None:
        """Apply all pending migrations.
        
        Raises:
            DatabaseError: If migration application fails.
        """
        applied = self._get_applied_migrations()
        
        for migration in self._migrations:
            name = (
                migration.name 
                if isinstance(migration, MigrationWrapper)
                else migration.__class__.__name__
            )
            if name not in applied:
                logger.info(f"Applying migration: {name}")
                try:
                    migration.upgrade(self.db)
                    self._record_migration(name)
                    logger.info(f"Successfully applied migration: {name}")
                except DatabaseError as e:
                    logger.error(f"Failed to apply migration {name}: {str(e)}")
                    # Try to clean up any partial changes
                    try:
                        migration.downgrade(self.db)
                    except DatabaseError:
                        pass  # Ignore cleanup errors
                    raise
    
    def revert_migrations(self) -> None:
        """Revert all migrations in reverse order.
        
        Raises:
            DatabaseError: If migration reversion fails.
        """
        applied = self._get_applied_migrations()
        
        for migration in reversed(self._migrations):
            name = (
                migration.name 
                if isinstance(migration, MigrationWrapper)
                else migration.__class__.__name__
            )
            if name in applied:
                logger.info(f"Reverting migration: {name}")
                try:
                    migration.downgrade(self.db)
                    self._remove_migration_record(name)
                    logger.info(f"Successfully reverted migration: {name}")
                except DatabaseError as e:
                    logger.error(f"Failed to revert migration {name}: {str(e)}")
                    raise
