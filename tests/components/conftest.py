"""Shared fixtures and utilities for component tests."""
import json
import os
from datetime import datetime, timezone, UTC
import re

import pytest
from processing.embedchain_store import EmbedchainStore
from tests.config import get_test_settings
from db.connection import Database

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
    store = EmbedchainStore(token_path=settings.GMAIL_TOKEN_PATH)
    yield store

@pytest.fixture(autouse=True)
def setup_test_database():
    """Set up test database with sample data."""
    settings = get_test_settings()
    db = Database(settings.TEST_DATABASE_PATH)
    db.connect()
    
    try:
        with db.transaction() as conn:
            # Clear existing data
            conn.execute("DELETE FROM newsletters")
            conn.execute("DELETE FROM repositories")
            
            # Insert sample newsletters
            now = datetime.now(UTC)
            newsletters = [
                {
                    'email_id': 'test_email_1',
                    'subject': 'AI/ML Weekly Newsletter #1',
                    'content': """
                    Check out these awesome AI/ML projects:
                    
                    1. https://github.com/huggingface/transformers - State-of-the-art NLP
                    2. https://github.com/pytorch/pytorch - Deep learning framework
                    3. https://github.com/microsoft/DeepSpeed - Deep learning optimization
                    """,
                    'received_date': now.isoformat(),
                    'processed_date': None,
                    'storage_status': 'active',
                    'processing_status': 'completed',
                    'vector_id': None,
                    'metadata': json.dumps({
                        'source': 'test',
                        'importance': 'high'
                    })
                },
                {
                    'email_id': 'test_email_2',
                    'subject': 'AI/ML Weekly Newsletter #2',
                    'content': """
                    More great AI/ML repositories:
                    
                    1. https://github.com/tensorflow/tensorflow - Machine learning platform
                    2. https://github.com/scikit-learn/scikit-learn - ML tools
                    3. https://github.com/ray-project/ray - Distributed computing
                    """,
                    'received_date': now.isoformat(),
                    'processed_date': None,
                    'storage_status': 'active',
                    'processing_status': 'completed',
                    'vector_id': None,
                    'metadata': json.dumps({
                        'source': 'test',
                        'importance': 'high'
                    })
                }
            ]
            
            for newsletter in newsletters:
                conn.execute(
                    """
                    INSERT INTO newsletters 
                    (email_id, subject, content, received_date, processed_date,
                    storage_status, processing_status, vector_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        newsletter['email_id'],
                        newsletter['subject'],
                        newsletter['content'],
                        newsletter['received_date'],
                        newsletter['processed_date'],
                        newsletter['storage_status'],
                        newsletter['processing_status'],
                        newsletter['vector_id'],
                        newsletter['metadata']
                    )
                )
            
            # Insert sample repositories
            repositories = [
                {
                    'github_url': 'https://github.com/huggingface/transformers',
                    'name': 'transformers',
                    'description': 'State-of-the-art Natural Language Processing',
                    'first_seen_date': now.isoformat(),
                    'last_mentioned_date': now.isoformat(),
                    'mention_count': 1,
                    'vector_id': None,
                    'metadata': json.dumps({
                        'stars': 1000,
                        'forks': 500,
                        'language': 'Python',
                        'topics': ['nlp', 'machine-learning'],
                        'created_at': '2024-01-01T00:00:00Z',
                        'updated_at': '2024-01-02T00:00:00Z'
                    })
                },
                {
                    'github_url': 'https://github.com/pytorch/pytorch',
                    'name': 'pytorch',
                    'description': 'Deep Learning Framework',
                    'first_seen_date': now.isoformat(),
                    'last_mentioned_date': now.isoformat(),
                    'mention_count': 1,
                    'vector_id': None,
                    'metadata': json.dumps({
                        'stars': 2000,
                        'forks': 1000,
                        'language': 'Python',
                        'topics': ['deep-learning', 'machine-learning'],
                        'created_at': '2024-01-01T00:00:00Z',
                        'updated_at': '2024-01-02T00:00:00Z'
                    })
                }
            ]
            
            for repo in repositories:
                conn.execute(
                    """
                    INSERT INTO repositories
                    (github_url, first_seen_date, last_mentioned_date, mention_count,
                    vector_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        repo['github_url'],
                        repo['first_seen_date'],
                        repo['last_mentioned_date'],
                        repo['mention_count'],
                        repo['vector_id'],
                        repo['metadata']
                    )
                )
        
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
