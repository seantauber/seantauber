"""Test database connection functionality."""

import sqlite3
from pathlib import Path

import pytest

from db.connection import Database, DatabaseError


@pytest.fixture
def temp_db_path(tmp_path):
    """Provide temporary database path."""
    return str(tmp_path / "test.db")


def test_database_init_creates_directory(temp_db_path):
    """Test database directory creation during initialization."""
    db = Database(temp_db_path)
    assert Path(temp_db_path).parent.exists()


def test_connect_disconnect(temp_db_path):
    """Test basic connection and disconnection."""
    db = Database(temp_db_path)
    
    # Test connection
    db.connect()
    assert db._conn is not None
    
    # Test disconnection
    db.disconnect()
    assert db._conn is None


def test_transaction_commit(temp_db_path):
    """Test transaction commits."""
    db = Database(temp_db_path)
    
    # Create test table and insert data
    with db.transaction() as conn:
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO test (id) VALUES (?)", (1,))
    
    # Verify data was committed
    result = db.fetch_one("SELECT id FROM test WHERE id = ?", (1,))
    assert result is not None
    assert result["id"] == 1


def test_transaction_rollback(temp_db_path):
    """Test transaction rollbacks on error."""
    db = Database(temp_db_path)
    
    # Create test table
    db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
    
    # Attempt invalid insert that should rollback
    with pytest.raises(DatabaseError):
        with db.transaction() as conn:
            conn.execute("INSERT INTO test (id) VALUES (?)", (1,))
            # This should trigger rollback
            conn.execute("INSERT INTO invalid_table VALUES (?)", (2,))
    
    # Verify no data was committed
    result = db.fetch_one("SELECT id FROM test WHERE id = ?", (1,))
    assert result is None


def test_execute_query(temp_db_path):
    """Test basic query execution."""
    db = Database(temp_db_path)
    
    # Create test table
    db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
    db.execute("INSERT INTO test (id) VALUES (?)", (1,))
    
    # Verify data
    result = db.fetch_one("SELECT id FROM test WHERE id = ?", (1,))
    assert result is not None
    assert result["id"] == 1


def test_fetch_one_no_results(temp_db_path):
    """Test fetch_one with no results."""
    db = Database(temp_db_path)
    
    # Create empty table
    db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
    
    # Should return None for no results
    result = db.fetch_one("SELECT id FROM test WHERE id = ?", (1,))
    assert result is None


def test_fetch_all_multiple_rows(temp_db_path):
    """Test fetch_all with multiple rows."""
    db = Database(temp_db_path)
    
    # Create test table and insert multiple rows
    db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
    for i in range(3):
        db.execute("INSERT INTO test (id) VALUES (?)", (i,))
    
    # Fetch all rows
    results = db.fetch_all("SELECT id FROM test ORDER BY id")
    assert len(results) == 3
    assert [r["id"] for r in results] == [0, 1, 2]


def test_error_handling(temp_db_path):
    """Test error handling for invalid queries."""
    db = Database(temp_db_path)
    
    with pytest.raises(DatabaseError):
        db.execute("INVALID SQL")
        
    with pytest.raises(DatabaseError):
        db.fetch_one("SELECT * FROM nonexistent_table")
        
    with pytest.raises(DatabaseError):
        db.fetch_all("SELECT * FROM nonexistent_table")


def test_connection_error(temp_db_path):
    """Test handling of connection errors."""
    # Create invalid database file
    Path(temp_db_path).parent.mkdir(parents=True, exist_ok=True)
    with open(temp_db_path, "wb") as f:
        f.write(b"not a database")
    
    # Attempting to initialize with invalid database should raise error
    with pytest.raises(DatabaseError):
        Database(temp_db_path)
