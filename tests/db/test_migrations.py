"""Test database migration functionality."""

import pytest
from datetime import datetime

from db.connection import Database, DatabaseError
from db.migrations import Migration, MigrationManager, InitialMigration

@pytest.fixture
def db():
    """Fixture providing in-memory database instance."""
    return Database(":memory:")

@pytest.fixture
def migration_manager(db):
    """Fixture providing migration manager instance."""
    return MigrationManager(db)

def test_initial_migration_creates_tables(db, migration_manager):
    """Test initial migration creates all required tables."""
    # Apply migrations
    migration_manager.apply_migrations()
    
    # Verify migrations table exists and has initial migration recorded
    result = db.fetch_one(
        "SELECT name FROM migrations WHERE name = ?",
        ("InitialMigration",)
    )
    assert result is not None
    
    # Verify all required tables were created
    tables = [
        "migrations",
        "newsletters",
        "repositories",
        "topics",
        "repository_categories"
    ]
    
    for table in tables:
        result = db.fetch_one("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table,))
        assert result is not None, f"Table {table} was not created"

def test_migration_tracking(db, migration_manager):
    """Test migration application is properly tracked."""
    # Apply migrations
    migration_manager.apply_migrations()
    
    # Verify migration was recorded
    result = db.fetch_one(
        "SELECT name, applied_at FROM migrations WHERE name = ?",
        ("InitialMigration",)
    )
    assert result is not None
    assert isinstance(datetime.fromisoformat(result["applied_at"]), datetime)

def test_migration_reversion(db, migration_manager):
    """Test migration reversion removes tables."""
    # Apply and then revert migrations
    migration_manager.apply_migrations()
    migration_manager.revert_migrations()
    
    # Verify all tables were removed
    tables = [
        "migrations",
        "newsletters",
        "repositories",
        "topics",
        "repository_categories"
    ]
    
    for table in tables:
        result = db.fetch_one("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table,))
        assert result is None, f"Table {table} was not removed"

def test_duplicate_migration_handling(db, migration_manager):
    """Test handling of duplicate migration applications."""
    # Apply migrations twice
    migration_manager.apply_migrations()
    migration_manager.apply_migrations()
    
    # Verify migration was only recorded once
    results = db.fetch_all(
        "SELECT name FROM migrations WHERE name = ?",
        ("InitialMigration",)
    )
    assert len(results) == 1

def test_failed_migration_handling(db):
    """Test handling of failed migrations."""
    class FailingMigration(Migration):
        def upgrade(self, db):
            raise DatabaseError("Simulated migration failure")
        
        def downgrade(self, db):
            pass
    
    class CustomMigrationManager(MigrationManager):
        def __init__(self, db):
            super().__init__(db)
            self._migrations = [FailingMigration()]
    
    manager = CustomMigrationManager(db)
    
    with pytest.raises(DatabaseError):
        manager.apply_migrations()
    
    # Verify migrations table doesn't exist
    result = db.fetch_one("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='migrations'
    """)
    assert result is None, "Migrations table should not exist after failed migration"

def test_table_constraints(db, migration_manager):
    """Test foreign key constraints are properly created."""
    # Apply migrations
    migration_manager.apply_migrations()
    
    # Test topics self-reference constraint
    with pytest.raises(DatabaseError):
        db.execute("""
            INSERT INTO topics 
            (name, first_seen_date, last_seen_date, parent_topic_id)
            VALUES (?, ?, ?, ?)
        """, (
            "test_topic",
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat(),
            999  # Non-existent parent_topic_id
        ))
    
    # Test repository_categories constraints
    with pytest.raises(DatabaseError):
        db.execute("""
            INSERT INTO repository_categories 
            (repository_id, topic_id, confidence_score)
            VALUES (?, ?, ?)
        """, (999, 999, 1.0))  # Non-existent repository_id and topic_id

def test_newsletter_schema(db, migration_manager):
    """Test newsletter table schema and constraints."""
    # Apply migrations
    migration_manager.apply_migrations()
    
    # Test unique email_id constraint
    db.execute("""
        INSERT INTO newsletters 
        (email_id, received_date, storage_status)
        VALUES (?, ?, ?)
    """, (
        "test@example.com",
        datetime.utcnow().isoformat(),
        "active"
    ))
    
    # Attempt to insert duplicate email_id
    with pytest.raises(DatabaseError):
        db.execute("""
            INSERT INTO newsletters 
            (email_id, received_date, storage_status)
            VALUES (?, ?, ?)
        """, (
            "test@example.com",
            datetime.utcnow().isoformat(),
            "active"
        ))

def test_repository_schema(db, migration_manager):
    """Test repository table schema and constraints."""
    # Apply migrations
    migration_manager.apply_migrations()
    
    # Test unique github_url constraint
    db.execute("""
        INSERT INTO repositories 
        (github_url, first_seen_date, last_mentioned_date)
        VALUES (?, ?, ?)
    """, (
        "https://github.com/test/repo",
        datetime.utcnow().isoformat(),
        datetime.utcnow().isoformat()
    ))
    
    # Attempt to insert duplicate github_url
    with pytest.raises(DatabaseError):
        db.execute("""
            INSERT INTO repositories 
            (github_url, first_seen_date, last_mentioned_date)
            VALUES (?, ?, ?)
        """, (
            "https://github.com/test/repo",
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        ))
