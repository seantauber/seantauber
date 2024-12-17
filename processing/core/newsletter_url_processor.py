"""Newsletter URL content processing module."""

import logging
from datetime import datetime, UTC, timedelta
from typing import List, Dict, Optional, Tuple

from db.connection import Database
from processing.core.url_content_fetcher import UrlContentFetcher, UrlContent

logger = logging.getLogger(__name__)

class NewsletterUrlProcessor:
    """Processor for handling URLs found in newsletters."""
    
    def __init__(self, db: Optional[Database] = None):
        """Initialize newsletter URL processor.
        
        Args:
            db: Optional database connection. If None, creates new connection.
        """
        self.db = db or Database()
        self.url_fetcher = UrlContentFetcher()
    
    async def fetch_and_cache_url_content(
        self,
        url: str,
        newsletter_id: int,
        expires_in_hours: int = 24
    ) -> Optional[str]:
        """Fetch and cache content from a URL.
        
        Args:
            url: URL to fetch content from
            newsletter_id: ID of newsletter containing the URL
            expires_in_hours: Hours until cache expires
            
        Returns:
            Fetched content if successful, None otherwise
        """
        try:
            # Check cache first
            cached = self.db.fetch_one(
                """
                SELECT content 
                FROM content_cache 
                WHERE url = ? AND expires_at > ?
                """,
                (url, datetime.now(UTC).isoformat())
            )
            
            if cached:
                return cached['content']
            
            # Fetch new content
            url_content = await self.url_fetcher.fetch_url_content(url)
            if url_content.error:
                logger.warning(f"Error fetching {url}: {url_content.error}")
                return None
            
            # Cache the content
            expires_at = datetime.now(UTC) + timedelta(hours=expires_in_hours)
            self.db.execute(
                """
                INSERT INTO content_cache (
                    url, content_type, content, last_accessed,
                    expires_at, newsletter_id, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    content = excluded.content,
                    last_accessed = excluded.last_accessed,
                    expires_at = excluded.expires_at,
                    newsletter_id = excluded.newsletter_id
                """,
                (
                    url,
                    'text/markdown',
                    url_content.content,
                    datetime.now(UTC).isoformat(),
                    expires_at.isoformat(),
                    newsletter_id,
                    'newsletter'
                )
            )
            
            return url_content.content
            
        except Exception as e:
            logger.error(f"Failed to fetch/cache content from {url}: {str(e)}")
            return None
    
    async def process_urls(
        self,
        urls: List[str],
        newsletter_id: int
    ) -> List[Dict[str, str]]:
        """Process a list of URLs from a newsletter.
        
        Args:
            urls: List of URLs to process
            newsletter_id: ID of newsletter containing the URLs
            
        Returns:
            List of dictionaries containing URL and content
        """
        results = []
        for url in urls:
            try:
                content = await self.fetch_and_cache_url_content(
                    url,
                    newsletter_id
                )
                if content:
                    results.append({
                        "url": url,
                        "content": content
                    })
            except Exception as e:
                logger.error(f"Failed to process URL {url}: {str(e)}")
                continue
        
        return results
