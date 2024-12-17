"""URL content fetching using requests and BeautifulSoup."""

import logging
import re
from typing import Optional, List
from datetime import datetime, UTC

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from pydantic import BaseModel, Field, HttpUrl

logger = logging.getLogger(__name__)

class UrlContent(BaseModel):
    """Model for URL content."""
    url: HttpUrl
    content: str
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: Optional[str] = None

class UrlContentFetcher:
    """Component for fetching content from URLs."""
    
    def __init__(self, timeout: int = 10):
        """Initialize URL content fetcher.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
    
    async def fetch_url_content(self, url: str) -> UrlContent:
        """Fetch content from a URL.
        
        Args:
            url: URL to fetch content from
            
        Returns:
            UrlContent object containing the fetched content
        """
        try:
            # Fetch the URL content
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML and convert to markdown
            soup = BeautifulSoup(response.content, 'html.parser')
            html_content = str(soup)
            markdown_content = md(html_content)
            
            return UrlContent(
                url=url,
                content=markdown_content
            )
            
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {str(e)}")
            return UrlContent(
                url=url,
                content="",
                error=str(e)
            )
    
    async def fetch_multiple_urls(self, urls: List[str]) -> List[UrlContent]:
        """Fetch content from multiple URLs.
        
        Args:
            urls: List of URLs to fetch content from
            
        Returns:
            List of UrlContent objects
        """
        results = []
        for url in urls:
            result = await self.fetch_url_content(url)
            results.append(result)
        return results

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text content.
        
        Args:
            text: Text content to extract URLs from
            
        Returns:
            List of extracted URLs
        """
        try:
            # Use regex to find URLs
            url_pattern = re.compile(
                r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            )
            urls = url_pattern.findall(text)
            return [url.strip('.,()[]{}') for url in urls]
        except Exception as e:
            logger.error(f"Error extracting URLs: {str(e)}")
            return []
