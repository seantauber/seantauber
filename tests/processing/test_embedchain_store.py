"""Tests for EmbedchainStore."""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from processing.embedchain_store import EmbedchainStore

@pytest.fixture
def mock_app():
    """Mock App instance."""
    with patch('processing.embedchain_store.App') as mock:
        yield mock

@pytest.fixture
def mock_gmail_service():
    """Mock Gmail service."""
    with patch('processing.embedchain_store.build') as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        yield mock_service

@pytest.fixture
def mock_credentials():
    """Mock Credentials."""
    with patch('processing.embedchain_store.Credentials') as mock:
        mock.from_authorized_user_file.return_value = MagicMock()
        yield mock

@pytest.fixture
def store(mock_app, mock_gmail_service, mock_credentials):
    """Create EmbedchainStore instance with mocked dependencies."""
    return EmbedchainStore(credentials_path=".credentials/credentials.json")

@pytest.fixture
def sample_gmail_message():
    """Sample Gmail message data."""
    return {
        'id': 'msg123',
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Newsletter'},
                {'name': 'From', 'value': 'sender@example.com'},
                {'name': 'Date', 'value': '2024-01-15'}
            ],
            'parts': [
                {
                    'body': {
                        'data': 'VGVzdCBjb250ZW50'  # Base64 encoded "Test content"
                    }
                }
            ]
        }
    }

@pytest.fixture
def sample_repository():
    """Sample repository data."""
    return {
        'github_url': 'https://github.com/test/repo',
        'description': 'Sample repository description',
        'first_seen_date': '2024-01-15'
    }

@pytest.mark.asyncio
async def test_get_label_id(store, mock_gmail_service):
    """Test getting Gmail label ID."""
    # Setup
    mock_gmail_service.users().labels().list().execute.return_value = {
        'labels': [
            {'id': 'label123', 'name': 'GenAI News'}
        ]
    }

    # Execute
    label_id = store._get_label_id()

    # Verify
    assert label_id == 'label123'
    # Verify that list was called with userId='me' and execute was called
    mock_gmail_service.users().labels().list.assert_called_with(userId='me')
    mock_gmail_service.users().labels().list().execute.assert_called_once()

@pytest.mark.asyncio
async def test_load_and_store_newsletters(store, mock_gmail_service, mock_app, sample_gmail_message):
    """Test loading and storing newsletters."""
    # Setup
    mock_gmail_service.users().labels().list().execute.return_value = {
        'labels': [{'id': 'label123', 'name': 'GenAI News'}]
    }
    mock_gmail_service.users().messages().list().execute.return_value = {
        'messages': [{'id': 'msg123'}]
    }
    mock_gmail_service.users().messages().get().execute.return_value = sample_gmail_message
    
    mock_app_instance = mock_app.return_value
    mock_app_instance.add.return_value = 'vector123'

    # Execute
    vector_ids = await store.load_and_store_newsletters(max_results=1)

    # Verify
    assert vector_ids == ['vector123']
    mock_app_instance.add.assert_called_once()
    assert mock_app_instance.add.call_args[1]['metadata']['email_id'] == 'msg123'

@pytest.mark.asyncio
async def test_store_repository(store, mock_app, sample_repository):
    """Test storing repository in vector storage."""
    # Setup
    mock_app_instance = mock_app.return_value
    mock_app_instance.add.return_value = 'vector456'

    # Execute
    vector_id = await store.store_repository(sample_repository)

    # Verify
    assert vector_id == 'vector456'
    mock_app_instance.add.assert_called_once_with(
        content=sample_repository['description'],
        metadata={
            'github_url': sample_repository['github_url'],
            'first_seen_date': sample_repository['first_seen_date']
        }
    )

@pytest.mark.asyncio
async def test_query_newsletters(store, mock_app):
    """Test querying newsletters."""
    # Setup
    mock_app_instance = mock_app.return_value
    expected_results = [
        {'content': 'Newsletter 1 content'},
        {'content': 'Newsletter 2 content'}
    ]
    mock_app_instance.query.return_value = expected_results

    # Execute
    results = await store.query_newsletters('test query', limit=2)

    # Verify
    assert results == expected_results
    mock_app_instance.query.assert_called_once_with('test query', top_k=2)

@pytest.mark.asyncio
async def test_query_repositories(store, mock_app):
    """Test querying repositories."""
    # Setup
    mock_app_instance = mock_app.return_value
    expected_results = [
        {'content': 'Repository 1 content'},
        {'content': 'Repository 2 content'}
    ]
    mock_app_instance.query.return_value = expected_results

    # Execute
    results = await store.query_repositories('test query', limit=2)

    # Verify
    assert results == expected_results
    mock_app_instance.query.assert_called_once_with('test query', top_k=2)

@pytest.mark.asyncio
async def test_load_and_store_newsletters_no_label(store, mock_gmail_service):
    """Test handling when newsletter label is not found."""
    # Setup
    mock_gmail_service.users().labels().list().execute.return_value = {
        'labels': [{'id': 'other_label', 'name': 'Other Label'}]
    }

    # Execute
    vector_ids = await store.load_and_store_newsletters()

    # Verify
    assert vector_ids == []

@pytest.mark.asyncio
async def test_load_and_store_newsletters_error(store, mock_gmail_service):
    """Test error handling when loading newsletters fails."""
    # Setup
    mock_gmail_service.users().labels().list().execute.side_effect = Exception("API error")

    # Execute and verify
    with pytest.raises(Exception, match="API error"):
        await store.load_and_store_newsletters()

@pytest.mark.asyncio
async def test_store_repository_error(store, mock_app, sample_repository):
    """Test error handling when storing repository fails."""
    # Setup
    mock_app_instance = mock_app.return_value
    mock_app_instance.add.side_effect = Exception("Storage error")

    # Execute and verify
    with pytest.raises(Exception, match="Storage error"):
        await store.store_repository(sample_repository)

@pytest.mark.asyncio
async def test_query_newsletters_error(store, mock_app):
    """Test error handling when querying newsletters fails."""
    # Setup
    mock_app_instance = mock_app.return_value
    mock_app_instance.query.side_effect = Exception("Query error")

    # Execute and verify
    with pytest.raises(Exception, match="Query error"):
        await store.query_newsletters('test query')

@pytest.mark.asyncio
async def test_query_repositories_error(store, mock_app):
    """Test error handling when querying repositories fails."""
    # Setup
    mock_app_instance = mock_app.return_value
    mock_app_instance.query.side_effect = Exception("Query error")

    # Execute and verify
    with pytest.raises(Exception, match="Query error"):
        await store.query_repositories('test query')
