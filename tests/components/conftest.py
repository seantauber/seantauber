"""Shared fixtures and utilities for component tests."""
import json
import os
from datetime import datetime, timezone, UTC
import re
import sqlite3

import pytest
from processing.embedchain_store import EmbedchainStore
from tests.config import get_test_settings
from db.connection import Database
from db.migrations import MigrationManager

def print_newsletter_summary(title: str, newsletters: list, show_content: bool = False):
    """Print summary of newsletters."""
    print(f"\n{title}:")
    print(f"Total Newsletters: {len(newsletters)}")
    
    github_url_pattern = re.compile(
        r'https://github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-_.]+/?(?:#[a-zA-Z0-9-_]*)?'
    )
    
    for n in newsletters:
        print(f"\n- Subject: {n['subject']}")
        print(f"  Received: {n['received_date']}")
        print(f"  Status: {n['processing_status']}")
        
        # Count GitHub URLs
        urls = github_url_pattern.findall(n['content'])
        print(f"  GitHub URLs Found: {len(urls)}")
        
        if show_content:
            # Format content preview
            content_preview = n['content'][:200].replace('\n', ' ').strip()
            print(f"  Content Preview: {content_preview}...")
            
            # Show found URLs
            if urls:
                print("  GitHub URLs:")
                for url in urls:
                    print(f"    - {url}")

def print_repository_summary(title: str, repositories: list, show_metadata: bool = False):
    """Print summary of repositories."""
    print(f"\n{title}:")
    print(f"Total Repositories: {len(repositories)}")
    for r in repositories:
        print(f"\n- URL: {r.get('url') or r.get('github_url')}")
        print(f"  Description: {r.get('description', '')}")
        if show_metadata and 'metadata' in r:
            print("  Metadata:")
            for key, value in r['metadata'].items():
                if key != 'readme_content':  # Skip long README content
                    print(f"    {key}: {value}")

def print_extraction_results(title: str, results: list):
    """Print extraction results."""
    print(f"\n{title}:")
    print(f"Total Results: {len(results)}")
    for r in results:
        print(f"\n- Newsletter: {r['newsletter_subject']}")
        print(f"  Repository: {r['repository_url']}")
        print(f"  Vector ID: {r['vector_id']}")
        if r['summary']:
            print("  Summary Generated: Yes")
        else:
            print("  Summary Generated: No")

@pytest.fixture
def vector_store() -> EmbedchainStore:
    """Initialize vector store for testing."""
    settings = get_test_settings()
    store = EmbedchainStore(vector_store_path=str(settings.VECTOR_STORAGE_PATH))
    yield store

def ensure_content_cache_table(db_path: str) -> None:
    """Ensure content_cache table exists with correct schema."""
    # Use direct SQLite connection to avoid transaction issues
    conn = sqlite3.connect(db_path)
    try:
        # Check if table exists
        result = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='content_cache'
        """).fetchone()
        
        if result:
            # Drop existing table to ensure clean schema
            conn.execute("DROP TABLE content_cache")
        
        # Create table and indexes in a single transaction
        conn.executescript("""
            BEGIN TRANSACTION;
            
            CREATE TABLE content_cache (
                id INTEGER PRIMARY KEY,
                url TEXT NOT NULL UNIQUE,
                content_type TEXT NOT NULL DEFAULT 'text/markdown',
                content TEXT NOT NULL,
                last_accessed TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                newsletter_id INTEGER,
                source TEXT NOT NULL DEFAULT 'manual',
                FOREIGN KEY (newsletter_id) REFERENCES newsletters(id)
                    ON DELETE SET NULL
                    ON UPDATE CASCADE
            );
            
            CREATE INDEX idx_content_cache_url 
            ON content_cache(url);
            
            CREATE INDEX idx_content_cache_expires 
            ON content_cache(expires_at);
            
            CREATE INDEX idx_content_cache_newsletter 
            ON content_cache(newsletter_id);
            
            COMMIT;
        """)
        
        # Verify table structure
        columns = conn.execute("PRAGMA table_info(content_cache)").fetchall()
        print("\nContent Cache Table Structure:")
        for col in columns:
            print(f"Column: {col[1]}, Type: {col[2]}")
        
    finally:
        conn.close()

@pytest.fixture(autouse=True)
def setup_test_database():
    """Set up test database with schema."""
    settings = get_test_settings()
    db_path = settings.TEST_DATABASE_PATH
    
    # Ensure content_cache table exists with correct schema
    ensure_content_cache_table(db_path)
    
    # Create database connection for tests
    db = Database(db_path)
    db.connect()
    
    try:
        yield db
    finally:
        db.disconnect()

@pytest.fixture
def sample_repository_data():
    """Sample repository data for testing."""
    now = datetime.now(UTC)
    return {
        'github_url': 'https://github.com/test/repo',
        'first_seen_date': now.isoformat(),
        'last_mentioned_date': now.isoformat(),
        'mention_count': 1,
        'vector_id': None,
        'metadata': json.dumps({
            'name': 'test-repo',
            'description': 'A test repository',
            'stars': 100,
            'forks': 50,
            'language': 'Python',
            'topics': ['testing', 'ai'],
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-02T00:00:00Z'
        })
    }
