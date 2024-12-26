"""Rate-limited GitHub API client."""

import logging
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import aiohttp
import base64

logger = logging.getLogger(__name__)

class RateLimitedGitHubClient:
    """GitHub API client with rate limiting."""
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    def __init__(self, token: str, calls_per_hour: int = 1000):
        """Initialize GitHub client.
        
        Args:
            token: GitHub API token
            calls_per_hour: Maximum API calls per hour (default 1000)
        """
        self.token = token
        self.calls_per_hour = calls_per_hour
        self.calls = []
        self.lock = asyncio.Lock()
        
        # Session for API calls
        self.session = aiohttp.ClientSession(headers={
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        })
    
    async def _check_rate_limit(self):
        """Check and enforce rate limits."""
        async with self.lock:
            now = datetime.now()
            hour_ago = now - timedelta(hours=1)
            
            # Remove calls older than 1 hour
            self.calls = [t for t in self.calls if t > hour_ago]
            
            # If at limit, wait until oldest call expires
            if len(self.calls) >= self.calls_per_hour:
                sleep_time = (self.calls[0] - hour_ago).total_seconds()
                logger.warning(f"Rate limit reached, waiting {sleep_time} seconds")
                await asyncio.sleep(sleep_time)
            
            # Record this call
            self.calls.append(now)
    
    async def fetch_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch repository metadata from GitHub API.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary containing repository metadata
            
        Raises:
            Exception: If API request fails
        """
        await self._check_rate_limit()
        
        async with self.session.get(
            f'https://api.github.com/repos/{owner}/{repo}'
        ) as response:
            if response.status != 200:
                raise Exception(f"GitHub API error: {response.status}")
            return await response.json()
    
    async def fetch_readme(self, owner: str, repo: str) -> Optional[str]:
        """Fetch repository README content.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            README content if available, None otherwise
            
        Raises:
            Exception: If API request fails
        """
        await self._check_rate_limit()
        
        async with self.session.get(
            f'https://api.github.com/repos/{owner}/{repo}/readme'
        ) as response:
            if response.status == 200:
                data = await response.json()
                return base64.b64decode(data['content']).decode('utf-8')
            elif response.status == 404:
                return None
            else:
                raise Exception(f"GitHub API error: {response.status}")
    
    async def get_repository_data(self, repo_url: str) -> Dict[str, Any]:
        """Get complete repository data including metadata and README.
        
        Args:
            repo_url: Full GitHub repository URL
            
        Returns:
            Dictionary containing repository data
            
        Raises:
            Exception: If URL parsing or API requests fail
        """
        # Extract owner and repo from URL
        try:
            _, _, _, owner, repo = repo_url.rstrip('/').split('/')
        except ValueError:
            raise Exception(f"Invalid GitHub URL: {repo_url}")
        
        # Fetch data
        repo_data = await self.fetch_repository(owner, repo)
        readme = await self.fetch_readme(owner, repo)
        
        return {
            "name": repo_data['name'],
            "full_name": repo_data['full_name'],
            "description": repo_data['description'] or "",
            "stars": repo_data['stargazers_count'],
            "forks": repo_data['forks_count'],
            "language": repo_data['language'],
            "topics": repo_data['topics'],
            "readme_content": readme or "",
            "created_at": repo_data['created_at'],
            "updated_at": repo_data['updated_at']
        }
    
    async def close(self):
        """Close the client session."""
        await self.session.close()
