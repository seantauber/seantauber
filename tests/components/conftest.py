"""Shared fixtures and utilities for component tests."""
import json
import os
from datetime import datetime, timezone

import pytest
from processing.embedchain_store import EmbedchainStore
from tests.config import get_test_settings

def print_newsletter_summary(title: str, newsletters: list, show_content: bool = False):
    """Print summary of newsletters."""
    print(f"\n{title}:")
    print(f"Total Newsletters: {len(newsletters)}")
    for n in newsletters:
        print(f"\n- Subject: {n['subject']}")
        print(f"  Received: {n['received_date']}")
        print(f"  Status: {n['processing_status']}")
        if show_content:
            print(f"  Content Preview: {n['content'][:200]}...")

def print_repository_summary(title: str, repositories: list, show_metadata: bool = False):
    """Print summary of repositories."""
    print(f"\n{title}:")
    print(f"Total Repositories: {len(repositories)}")
    for r in repositories:
        print(f"\n- URL: {r['url']}")
        print(f"  Description: {r['description']}")
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
