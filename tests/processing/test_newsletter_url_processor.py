"""Tests for newsletter URL processor."""

import pytest
from datetime import datetime, UTC
from unittest.mock import patch, Mock, AsyncMock

from processing.core.newsletter_url_processor import NewsletterUrlProcessor
from processing.core.url_content_fetcher import UrlContent

@pytest.fixture
def processor():
    """Create newsletter URL processor instance."""
    return NewsletterUrlProcessor()

@pytest.fixture
def mock_url_content():
    """Create mock URL content."""
    return UrlContent(
        url="https://example.com/article",
        content="# Test Article\n\nThis is a test article.",
        fetched_at=datetime.now(UTC)
    )

@pytest.mark.asyncio
async def test_fetch_and_cache_url_content(processor, mock_url_content):
    """Test fetching and caching URL content."""
    url = "https://example.com/article"
    newsletter_id = 1
    
    # Mock database to simulate cache miss then hit
    processor.db.fetch_one = Mock(side_effect=[None, {"content": mock_url_content.content}])
    
    # Mock URL fetcher
    with patch('processing.core.url_content_fetcher.UrlContentFetcher.fetch_url_content', 
               new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_url_content
        
        # First fetch should get from URL
        content = await processor.fetch_and_cache_url_content(
            url,
            newsletter_id
        )
        assert content == mock_url_content.content
        mock_fetch.assert_called_once()
        
        # Second fetch should get from cache
        content = await processor.fetch_and_cache_url_content(
            url,
            newsletter_id
        )
        assert content == mock_url_content.content
        mock_fetch.assert_called_once()  # No additional fetch

@pytest.mark.asyncio
async def test_fetch_and_cache_url_content_error(processor):
    """Test handling URL fetch errors."""
    url = "https://invalid.example.com"
    newsletter_id = 1
    
    # Mock database for cache miss
    processor.db.fetch_one = Mock(return_value=None)
    
    # Mock URL fetcher to return error
    with patch('processing.core.url_content_fetcher.UrlContentFetcher.fetch_url_content',
               new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = UrlContent(
            url=url,
            content="",
            error="Connection failed",
            fetched_at=datetime.now(UTC)
        )
        
        content = await processor.fetch_and_cache_url_content(
            url,
            newsletter_id
        )
        assert content is None

@pytest.mark.asyncio
async def test_process_urls(processor, mock_url_content):
    """Test processing multiple URLs."""
    urls = [
        "https://example.com/article1",
        "https://example.com/article2"
    ]
    newsletter_id = 1
    
    # Mock database for cache misses
    processor.db.fetch_one = Mock(return_value=None)
    
    # Mock URL fetcher
    with patch('processing.core.url_content_fetcher.UrlContentFetcher.fetch_url_content',
               new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_url_content
        
        results = await processor.process_urls(urls, newsletter_id)
        
        assert len(results) == 2
        assert all(r["url"] in urls for r in results)
        assert all(r["content"] == mock_url_content.content for r in results)
        assert mock_fetch.call_count == 2

@pytest.mark.asyncio
async def test_process_urls_with_errors(processor, mock_url_content):
    """Test processing URLs with some failures."""
    urls = [
        "https://example.com/good",
        "https://example.com/bad"
    ]
    newsletter_id = 1
    
    # Mock database for cache misses
    processor.db.fetch_one = Mock(return_value=None)
    
    async def mock_fetch(url):
        if "bad" in url:
            return UrlContent(
                url=url,
                content="",
                error="Failed",
                fetched_at=datetime.now(UTC)
            )
        return mock_url_content
    
    # Mock URL fetcher
    with patch('processing.core.url_content_fetcher.UrlContentFetcher.fetch_url_content',
               new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = mock_fetch
        
        results = await processor.process_urls(urls, newsletter_id)
        
        assert len(results) == 1
        assert results[0]["url"] == "https://example.com/good"
        assert results[0]["content"] == mock_url_content.content

@pytest.mark.asyncio
async def test_fetch_and_cache_url_content_database_error(processor, mock_url_content):
    """Test handling database errors during caching."""
    url = "https://example.com/article"
    newsletter_id = 1
    
    # Mock database to raise error
    processor.db.fetch_one = Mock(side_effect=Exception("Database error"))
    
    # Mock URL fetcher
    with patch('processing.core.url_content_fetcher.UrlContentFetcher.fetch_url_content',
               new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_url_content
        
        content = await processor.fetch_and_cache_url_content(
            url,
            newsletter_id
        )
        assert content is None
