"""Tests for EmbedchainStore."""

import asyncio
import pytest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch, MagicMock, call
from processing.embedchain_store import EmbedchainStore

@pytest.fixture
def mock_app():
    """Mock App instance."""
    with patch('processing.embedchain_store.App') as mock:
        yield mock

@pytest.fixture
def store(mock_app):
    """Create EmbedchainStore instance with mocked dependencies."""
    return EmbedchainStore(vector_store_path="/tmp/test_vector_store")

@pytest.fixture
def sample_repository():
    """Sample repository data."""
    return {
        'name': 'test-repo',
        'github_url': 'https://github.com/test/repo',
        'description': 'Sample repository description',
        'metadata': {
            'language': 'Python',
            'topics': ['ai', 'machine-learning']
        },
        'summary': {
            'primary_purpose': 'Testing',
            'technical_domain': 'Machine Learning'
        }
    }

@pytest.mark.asyncio
async def test_concurrent_store_repository(store, mock_app, sample_repository):
    """Test concurrent repository storage operations."""
    # Setup
    mock_app_instance = mock_app.return_value
    mock_app_instance.add.return_value = 'vector456'
    num_concurrent = 5
    
    async def store_concurrent():
        tasks = []
        for i in range(num_concurrent):
            repo = sample_repository.copy()
            repo['github_url'] = f"https://github.com/test/repo{i}"
            tasks.append(store.store_repository(repo))
        return await asyncio.gather(*tasks)
    
    # Execute
    vector_ids = await store_concurrent()
    
    # Verify
    assert len(vector_ids) == num_concurrent
    assert all(vid == 'vector456' for vid in vector_ids)
    assert mock_app_instance.add.call_count == num_concurrent

@pytest.mark.asyncio
async def test_concurrent_query_operations(store, mock_app):
    """Test concurrent query operations."""
    # Setup
    mock_app_instance = mock_app.return_value
    mock_app_instance.query.return_value = [{'content': 'Test content'}]
    num_concurrent = 5
    
    async def query_concurrent():
        tasks = []
        for i in range(num_concurrent):
            if i % 2 == 0:
                tasks.append(store.query_newsletters(f'test query {i}'))
            else:
                tasks.append(store.query_repositories(f'test query {i}'))
        return await asyncio.gather(*tasks)
    
    # Execute
    results = await query_concurrent()
    
    # Verify
    assert len(results) == num_concurrent
    assert all(len(r) > 0 for r in results)
    assert mock_app_instance.query.call_count == num_concurrent

@pytest.mark.asyncio
async def test_concurrent_mixed_operations(store, mock_app, sample_repository):
    """Test concurrent mixed operations (store and query)."""
    # Setup
    mock_app_instance = mock_app.return_value
    mock_app_instance.add.return_value = 'vector456'
    mock_app_instance.query.return_value = [{'content': 'Test content'}]
    num_concurrent = 6
    
    async def mixed_concurrent():
        tasks = []
        for i in range(num_concurrent):
            if i % 3 == 0:
                repo = sample_repository.copy()
                repo['github_url'] = f"https://github.com/test/repo{i}"
                tasks.append(store.store_repository(repo))
            elif i % 3 == 1:
                tasks.append(store.query_newsletters(f'test query {i}'))
            else:
                tasks.append(store.query_repositories(f'test query {i}'))
        return await asyncio.gather(*tasks)
    
    # Execute
    results = await mixed_concurrent()
    
    # Verify
    assert len(results) == num_concurrent
    store_count = len([r for r in results if isinstance(r, str)])  # vector IDs are strings
    query_count = len([r for r in results if isinstance(r, list)])  # query results are lists
    assert store_count == num_concurrent // 3
    assert query_count == 2 * (num_concurrent // 3)

@pytest.mark.asyncio
async def test_concurrent_cache_access(store, mock_app, sample_repository):
    """Test concurrent access to repository cache."""
    # Setup
    mock_app_instance = mock_app.return_value
    mock_app_instance.add.return_value = 'vector456'
    mock_app_instance.query.return_value = [sample_repository['github_url']]
    num_concurrent = 5
    
    # First store repositories
    repos = []
    for i in range(num_concurrent):
        repo = sample_repository.copy()
        repo['github_url'] = f"https://github.com/test/repo{i}"
        repos.append(repo)
        await store.store_repository(repo)
    
    # Then test concurrent cache access through queries
    async def query_concurrent():
        tasks = []
        for i in range(num_concurrent):
            tasks.append(store.query_repositories(f'test query {i}'))
        return await asyncio.gather(*tasks)
    
    # Execute
    results = await query_concurrent()
    
    # Verify
    assert len(results) == num_concurrent
    assert all(len(r) > 0 for r in results)
    assert mock_app_instance.query.call_count == num_concurrent
