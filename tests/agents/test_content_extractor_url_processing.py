"""Tests for URL content processing in ContentExtractorAgent."""

import pytest
from datetime import datetime, UTC
from unittest.mock import patch, Mock, AsyncMock

from agents.content_extractor import ContentExtractorAgent
from processing.core.url_content_fetcher import UrlContent

@pytest.fixture
def mock_url_content():
    """Create mock URL content."""
    return UrlContent(
        url="https://example.com/article",
        content="# Test Article\n\nThis is a test article.",
        fetched_at=datetime.now(UTC)
    )

@pytest.mark.asyncio
async def test_process_newsletter_with_mixed_content(mock_url_content):
    """Test processing newsletter with both GitHub repos and other URLs."""
    content = """
    Check out this repo:
    https://github.com/user/repo1
    
    And this article:
    https://example.com/article
    """
    email_id = "test123"
    
    # Create agent with mocked database
    db = Mock()
    db.fetch_one = Mock(return_value={"id": 1})  # For newsletter lookup
    db.transaction = Mock()
    agent = ContentExtractorAgent("fake-token", db=db)
    
    # Mock URL processor
    with patch('processing.core.newsletter_url_processor.NewsletterUrlProcessor.process_urls',
               new_callable=AsyncMock) as mock_process_urls:
        mock_process_urls.return_value = [{
            "url": "https://example.com/article",
            "content": mock_url_content.content
        }]
        
        # Mock repository processing
        with patch.object(agent, 'fetch_repository_metadata',
                         new_callable=AsyncMock) as mock_repo_fetch:
            mock_repo_fetch.return_value = {
                "name": "repo1",
                "full_name": "user/repo1",
                "description": "Test repo",
                "stars": 100,
                "forks": 10,
                "language": "Python",
                "topics": ["ai"],
                "readme_content": "# Test\nRepo content",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-02T00:00:00Z"
            }
            
            # Mock repository summary generation
            with patch.object(agent, 'generate_repository_summary',
                            new_callable=AsyncMock) as mock_summary:
                mock_summary.return_value.is_genai = True
                mock_summary.return_value.model_dump = Mock(return_value={})
                
                results = await agent.process_newsletter_content(email_id, content)
                
                assert len(results) == 1
                assert len(results[0]["repositories"]) == 1
                assert len(results[0]["urls"]) == 1
                
                assert results[0]["urls"][0]["url"] == "https://example.com/article"
                assert results[0]["urls"][0]["content"] == mock_url_content.content

@pytest.mark.asyncio
async def test_process_newsletter_only_urls(mock_url_content):
    """Test processing newsletter with only non-GitHub URLs."""
    content = """
    Check out these articles:
    https://example.com/article1
    https://example.com/article2
    """
    email_id = "test123"
    
    # Create agent with mocked database
    db = Mock()
    db.fetch_one = Mock(return_value={"id": 1})  # For newsletter lookup
    agent = ContentExtractorAgent("fake-token", db=db)
    
    # Mock URL processor
    with patch('processing.core.newsletter_url_processor.NewsletterUrlProcessor.process_urls',
               new_callable=AsyncMock) as mock_process_urls:
        mock_process_urls.return_value = [
            {
                "url": "https://example.com/article1",
                "content": mock_url_content.content
            },
            {
                "url": "https://example.com/article2",
                "content": mock_url_content.content
            }
        ]
        
        results = await agent.process_newsletter_content(email_id, content)
        
        assert len(results) == 1
        assert len(results[0]["repositories"]) == 0
        assert len(results[0]["urls"]) == 2
        
        assert all(r["content"] == mock_url_content.content for r in results[0]["urls"])

@pytest.mark.asyncio
async def test_process_newsletter_url_errors():
    """Test processing newsletter with URL fetch errors."""
    content = """
    Check out these articles:
    https://example.com/good
    https://example.com/bad
    """
    email_id = "test123"
    
    # Create agent with mocked database
    db = Mock()
    db.fetch_one = Mock(return_value={"id": 1})  # For newsletter lookup
    agent = ContentExtractorAgent("fake-token", db=db)
    
    # Mock URL processor to simulate some failures
    with patch('processing.core.newsletter_url_processor.NewsletterUrlProcessor.process_urls',
               new_callable=AsyncMock) as mock_process_urls:
        mock_process_urls.return_value = [
            {
                "url": "https://example.com/good",
                "content": "Good content"
            }
        ]
        
        results = await agent.process_newsletter_content(email_id, content)
        
        assert len(results) == 1
        assert len(results[0]["repositories"]) == 0
        assert len(results[0]["urls"]) == 1
        assert results[0]["urls"][0]["url"] == "https://example.com/good"

@pytest.mark.asyncio
async def test_process_newsletter_no_urls():
    """Test processing newsletter with no URLs."""
    content = "Just some text without any URLs"
    email_id = "test123"
    
    # Create agent with mocked database
    db = Mock()
    db.fetch_one = Mock(return_value={"id": 1})  # For newsletter lookup
    agent = ContentExtractorAgent("fake-token", db=db)
    
    results = await agent.process_newsletter_content(email_id, content)
    
    assert len(results) == 1
    assert len(results[0]["repositories"]) == 0
    assert len(results[0]["urls"]) == 0
