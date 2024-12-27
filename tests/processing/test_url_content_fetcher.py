"""Tests for URL content fetcher."""

import pytest
from datetime import datetime, UTC
from unittest.mock import patch, Mock

from processing.core.url_content_fetcher import UrlContentFetcher, UrlContent

@pytest.fixture
def fetcher():
    """Create URL content fetcher instance."""
    return UrlContentFetcher()

@pytest.fixture
def mock_response():
    """Create mock response with HTML content."""
    mock = Mock()
    mock.content = b"""
    <html>
        <body>
            <h1>Test Page</h1>
            <p>This is a test paragraph.</p>
            <a href="https://example.com">Link</a>
        </body>
    </html>
    """
    return mock

@pytest.mark.asyncio
async def test_fetch_url_content_success(fetcher, mock_response):
    """Test successful URL content fetching."""
    url = "https://example.com"
    
    with patch('requests.get', return_value=mock_response) as mock_get:
        result = await fetcher.fetch_url_content(url)
        
        assert isinstance(result, UrlContent)
        assert result.url == url
        assert "Test Page" in result.content
        assert "test paragraph" in result.content
        assert isinstance(result.fetched_at, datetime)
        assert result.error is None
        
        mock_get.assert_called_once_with(url, timeout=10)

@pytest.mark.asyncio
async def test_fetch_url_content_error(fetcher):
    """Test URL content fetching with error."""
    url = "https://invalid.example.com"
    
    with patch('requests.get', side_effect=Exception("Test error")):
        result = await fetcher.fetch_url_content(url)
        
        assert isinstance(result, UrlContent)
        assert result.url == url
        assert result.content == ""
        assert result.error == "Test error"

@pytest.mark.asyncio
async def test_fetch_multiple_urls(fetcher, mock_response):
    """Test fetching content from multiple URLs."""
    urls = [
        "https://example1.com",
        "https://example2.com"
    ]
    
    with patch('requests.get', return_value=mock_response):
        results = await fetcher.fetch_multiple_urls(urls)
        
        assert len(results) == 2
        assert all(isinstance(r, UrlContent) for r in results)
        assert all("Test Page" in r.content for r in results)

def test_extract_urls(fetcher):
    """Test URL extraction from text."""
    text = """
    Check out these links:
    https://example.com/page1
    Some text https://example.com/page2.
    And https://example.com/page3!
    Invalid: not-a-url.com
    """
    
    urls = fetcher.extract_urls(text)
    
    assert len(urls) == 3
    assert "https://example.com/page1" in urls
    assert "https://example.com/page2" in urls
    assert "https://example.com/page3" in urls

def test_extract_urls_no_matches(fetcher):
    """Test URL extraction with no matches."""
    text = "No URLs in this text"
    
    urls = fetcher.extract_urls(text)
    
    assert len(urls) == 0

def test_extract_urls_error(fetcher):
    """Test URL extraction with error."""
    with patch('re.compile', side_effect=Exception("Test error")):
        urls = fetcher.extract_urls("some text")
        assert len(urls) == 0

def test_should_skip_url(fetcher):
    """Test URL filtering for subscription-related patterns."""
    # URLs that should be skipped
    skip_urls = [
        "https://example.com/subscribe",
        "https://example.com/unsubscribe",
        "https://example.com/preferences",
        "https://example.com/manage",
        "https://example.com/settings",
        "https://example.com/subscription",
        "https://example.com/opt-out",
        "https://example.com/opt-in",
        "https://example.com/email-settings",
        "https://example.com/newsletter"
    ]
    
    # URLs that should not be skipped
    allow_urls = [
        "https://example.com/article",
        "https://example.com/blog",
        "https://example.com/repository",
        "https://example.com/docs/subscription-model" # Technical content with subscription in name
    ]
    
    for url in skip_urls:
        assert fetcher.should_skip_url(url), f"Should skip {url}"
        
    for url in allow_urls:
        assert not fetcher.should_skip_url(url), f"Should not skip {url}"

@pytest.mark.asyncio
async def test_fetch_subscription_url(fetcher):
    """Test fetching content from subscription-related URLs."""
    url = "https://example.com/subscribe"
    
    result = await fetcher.fetch_url_content(url)
    
    assert isinstance(result, UrlContent)
    assert result.url == url
    assert result.content == ""
    assert result.error == "Skipped subscription-related URL"

def test_url_content_model_validation():
    """Test UrlContent model validation."""
    # Valid data
    data = {
        "url": "https://example.com",
        "content": "Test content",
        "fetched_at": datetime.now(UTC),
        "error": None
    }
    content = UrlContent(**data)
    assert content.url == data["url"]
    assert content.content == data["content"]
    
    # Invalid URL
    with pytest.raises(ValueError):
        UrlContent(url="not-a-url", content="test")
