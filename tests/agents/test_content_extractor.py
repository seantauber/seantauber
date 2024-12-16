import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import json

from pydantic_ai import Agent, RunContext
from agents.content_extractor import ContentExtractorAgent, ContentExtractionError
from processing.embedchain_store import EmbedchainStore

@pytest.fixture
def mock_embedchain_store():
    store = Mock(spec=EmbedchainStore)
    # Make store_repository return a coroutine
    async def mock_store_repository(data):
        return "vector_id_123"
    store.store_repository = mock_store_repository
    
    # Add query_repositories for migration testing
    async def mock_query_repositories(query, limit):
        return [
            {
                'metadata': {
                    'github_url': 'https://github.com/user1/repo1',
                    'first_seen_date': '2024-01-01T00:00:00Z',
                    'source_type': 'newsletter',
                    'source_id': 'email123'
                }
            }
        ]
    store.query_repositories = mock_query_repositories
    return store

@pytest.fixture
def mock_github_response():
    return {
        'name': 'test-repo',
        'full_name': 'user/test-repo',
        'description': 'A test repository',
        'stargazers_count': 100,
        'forks_count': 50,
        'language': 'Python',
        'topics': ['ai', 'machine-learning'],
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-02T00:00:00Z'
    }

@pytest.fixture
def mock_readme_response():
    return {
        'content': 'IyBUZXN0IFJlcG9zaXRvcnkKCkEgdGVzdCByZXBvc2l0b3J5IGZvciBBSS9NTC4='  # Base64 encoded
    }

@pytest.fixture
def mock_summary_response():
    return {
        'primary_purpose': 'Test AI/ML functionality',
        'key_technologies': ['python', 'pytorch', 'transformers'],
        'target_users': 'ML researchers and developers',
        'main_features': ['model training', 'inference', 'evaluation'],
        'technical_domain': 'Machine Learning'
    }

@pytest.fixture
def content_extractor(mock_embedchain_store):
    return ContentExtractorAgent(
        vector_store=mock_embedchain_store,
        github_token="test_token"
    )

@pytest.fixture
def sample_newsletter_content():
    return """
    Check out these awesome GenAI projects:
    
    1. https://github.com/user1/repo1 - A cool LLM project
    2. https://github.com/user2/repo2/ - Vector database implementation
    Not a repo: https://example.com
    Another repo: https://github.com/user3/repo3#readme
    """

def test_extract_repository_links(content_extractor, sample_newsletter_content):
    """Test that GitHub repository links are correctly extracted."""
    expected_repos = [
        "https://github.com/user1/repo1",
        "https://github.com/user2/repo2",
        "https://github.com/user3/repo3"
    ]
    
    result = content_extractor.extract_repository_links(sample_newsletter_content)
    assert isinstance(result, list)
    assert sorted(result) == sorted(expected_repos)

def test_extract_repository_links_no_repos(content_extractor):
    """Test handling of content with no repository links."""
    content = "No GitHub repos here, just some text https://example.com"
    result = content_extractor.extract_repository_links(content)
    assert isinstance(result, list)
    assert len(result) == 0

def test_extract_repository_links_invalid_content(content_extractor):
    """Test handling of invalid content."""
    with pytest.raises(ContentExtractionError):
        content_extractor.extract_repository_links(None)

@pytest.mark.asyncio
async def test_fetch_repository_metadata(
    content_extractor,
    mock_github_response,
    mock_readme_response
):
    """Test fetching repository metadata from GitHub API."""
    with patch('aiohttp.ClientSession.get') as mock_get:
        # Setup mock responses
        mock_get.side_effect = [
            AsyncMock(
                status=200,
                json=AsyncMock(return_value=mock_github_response)
            )(),
            AsyncMock(
                status=200,
                json=AsyncMock(return_value=mock_readme_response)
            )()
        ]
        
        metadata = await content_extractor.fetch_repository_metadata(
            "https://github.com/user/test-repo"
        )
        
        assert metadata['name'] == 'test-repo'
        assert metadata['description'] == 'A test repository'
        assert metadata['stars'] == 100
        assert metadata['forks'] == 50
        assert metadata['language'] == 'Python'
        assert metadata['topics'] == ['ai', 'machine-learning']
        assert metadata['readme_content'].startswith('# Test Repository')

@pytest.mark.asyncio
async def test_generate_repository_summary(
    content_extractor,
    mock_github_response,
    mock_summary_response
):
    """Test generating repository summary using LLM."""
    with patch.object(
        content_extractor.summarization_agent,
        'complete',
        return_value=AsyncMock(content=json.dumps(mock_summary_response))
    ):
        metadata = {
            **mock_github_response,
            'readme_content': '# Test Repository\n\nA test repository for AI/ML.'
        }
        
        summary = await content_extractor.generate_repository_summary(metadata)
        
        assert summary['primary_purpose'] == 'Test AI/ML functionality'
        assert 'python' in summary['key_technologies']
        assert summary['target_users'] == 'ML researchers and developers'
        assert 'model training' in summary['main_features']
        assert summary['technical_domain'] == 'Machine Learning'

@pytest.mark.asyncio
async def test_process_newsletter_content(
    content_extractor,
    sample_newsletter_content,
    mock_embedchain_store,
    mock_github_response,
    mock_readme_response,
    mock_summary_response
):
    """Test full newsletter content processing with summaries."""
    with patch('aiohttp.ClientSession.get') as mock_get:
        # Setup mock responses for each repository
        mock_get.side_effect = [
            # First repo metadata
            AsyncMock(status=200, json=AsyncMock(return_value=mock_github_response))(),
            AsyncMock(status=200, json=AsyncMock(return_value=mock_readme_response))(),
            # Second repo metadata
            AsyncMock(status=200, json=AsyncMock(return_value=mock_github_response))(),
            AsyncMock(status=200, json=AsyncMock(return_value=mock_readme_response))(),
            # Third repo metadata
            AsyncMock(status=200, json=AsyncMock(return_value=mock_github_response))(),
            AsyncMock(status=200, json=AsyncMock(return_value=mock_readme_response))()
        ]
        
        # Mock LLM summary generation
        with patch.object(
            content_extractor.summarization_agent,
            'complete',
            return_value=AsyncMock(content=json.dumps(mock_summary_response))
        ):
            result = await content_extractor.process_newsletter_content(
                email_id="test123",
                content=sample_newsletter_content
            )
    
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(repo, dict) for repo in result)
    assert all("url" in repo for repo in result)
    assert all("vector_id" in repo for repo in result)
    assert all("metadata" in repo for repo in result)
    assert all("summary" in repo for repo in result)
    
    # Verify summary structure
    for repo in result:
        summary = repo['summary']
        assert 'primary_purpose' in summary
        assert 'key_technologies' in summary
        assert 'target_users' in summary
        assert 'main_features' in summary
        assert 'technical_domain' in summary
    
    # Verify all repositories were processed
    expected_urls = [
        "https://github.com/user1/repo1",
        "https://github.com/user2/repo2",
        "https://github.com/user3/repo3"
    ]
    actual_urls = [repo["url"] for repo in result]
    assert sorted(actual_urls) == sorted(expected_urls)

@pytest.mark.asyncio
async def test_migrate_existing_repositories(
    content_extractor,
    mock_github_response,
    mock_readme_response,
    mock_summary_response
):
    """Test migration of existing repositories."""
    with patch('aiohttp.ClientSession.get') as mock_get:
        # Setup mock responses
        mock_get.side_effect = [
            AsyncMock(status=200, json=AsyncMock(return_value=mock_github_response))(),
            AsyncMock(status=200, json=AsyncMock(return_value=mock_readme_response))()
        ]
        
        # Mock LLM summary generation
        with patch.object(
            content_extractor.summarization_agent,
            'complete',
            return_value=AsyncMock(content=json.dumps(mock_summary_response))
        ):
            await content_extractor.migrate_existing_repositories()
    
    # Verify store_repository was called with correct data
    calls = [call[0][0] for call in content_extractor.vector_store.store_repository.call_args_list]
    assert len(calls) == 1
    
    repo_data = calls[0]
    assert repo_data['github_url'] == 'https://github.com/user1/repo1'
    assert 'summary' in repo_data
    assert repo_data['summary'] == mock_summary_response
    assert repo_data['metadata']['language'] == 'Python'
    assert repo_data['metadata']['topics'] == ['ai', 'machine-learning']

@pytest.mark.asyncio
async def test_process_newsletter_content_error(content_extractor):
    """Test error handling in newsletter content processing."""
    with pytest.raises(ContentExtractionError):
        await content_extractor.process_newsletter_content(
            email_id=None,
            content=None
        )

def test_validate_github_url(content_extractor):
    """Test GitHub URL validation."""
    valid_urls = [
        "https://github.com/user/repo",
        "https://github.com/user/repo/",
        "https://github.com/user/repo#readme"
    ]
    invalid_urls = [
        "https://example.com",
        "http://github.com/user",
        "https://github.com",
        None
    ]
    
    for url in valid_urls:
        assert content_extractor.validate_github_url(url) is True
    
    for url in invalid_urls:
        assert content_extractor.validate_github_url(url) is False

@pytest.mark.asyncio
async def test_fetch_repository_metadata_error(content_extractor):
    """Test error handling in repository metadata fetching."""
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.side_effect = Exception("API error")
        
        with pytest.raises(ContentExtractionError):
            await content_extractor.fetch_repository_metadata(
                "https://github.com/user/repo"
            )

@pytest.mark.asyncio
async def test_generate_repository_summary_error(
    content_extractor,
    mock_github_response
):
    """Test error handling in summary generation."""
    with patch.object(
        content_extractor.summarization_agent,
        'complete',
        side_effect=Exception("LLM error")
    ):
        metadata = {
            **mock_github_response,
            'readme_content': '# Test Repository\n\nA test repository for AI/ML.'
        }
        
        with pytest.raises(ContentExtractionError):
            await content_extractor.generate_repository_summary(metadata)
