import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, patch
import asyncio

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
    return store

@pytest.fixture
def content_extractor(mock_embedchain_store):
    return ContentExtractorAgent(vector_store=mock_embedchain_store)

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

def test_collect_metadata(content_extractor):
    """Test repository metadata collection."""
    repo_url = "https://github.com/user1/repo1"
    metadata = content_extractor.collect_metadata(repo_url)
    
    assert isinstance(metadata, dict)
    assert "url" in metadata
    assert metadata["url"] == repo_url
    assert "first_seen_date" in metadata
    # Verify it's a valid ISO format date
    datetime.fromisoformat(metadata["first_seen_date"])

@pytest.mark.asyncio
async def test_process_newsletter_content(content_extractor, sample_newsletter_content, mock_embedchain_store):
    """Test full newsletter content processing."""
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
    
    # Verify all repositories were processed
    expected_urls = [
        "https://github.com/user1/repo1",
        "https://github.com/user2/repo2",
        "https://github.com/user3/repo3"
    ]
    actual_urls = [repo["url"] for repo in result]
    assert sorted(actual_urls) == sorted(expected_urls)

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
