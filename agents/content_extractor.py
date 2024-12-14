import re
import logging
from datetime import datetime, UTC
from typing import List, Dict, Optional

from pydantic_ai import Agent, RunContext
from processing.embedchain_store import EmbedchainStore

logger = logging.getLogger(__name__)

class ContentExtractionError(Exception):
    """Raised when content extraction fails."""
    pass

class ContentExtractorAgent:
    """Agent responsible for extracting GitHub repositories from newsletter content."""
    
    def __init__(self, vector_store: EmbedchainStore):
        """Initialize the Content Extractor agent.
        
        Args:
            vector_store: Vector storage instance for content analysis
        """
        self.vector_store = vector_store
        self.agent = Agent(
            "openai:gpt-4",
            system_prompt=(
                "Extract and analyze GitHub repository links from newsletter content. "
                "Focus on identifying relevant AI/ML repositories and their context."
            )
        )
        
        # Regex for GitHub repository URLs
        self.github_url_pattern = re.compile(
            r'https://github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-_.]+/?(?:#[a-zA-Z0-9-_]*)?'
        )
    
    def validate_github_url(self, url: Optional[str]) -> bool:
        """Validate if a URL is a valid GitHub repository URL.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid GitHub repository URL, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
        return bool(self.github_url_pattern.match(url))
    
    def extract_repository_links(self, content: str) -> List[str]:
        """Extract GitHub repository links from content.
        
        Args:
            content: Newsletter content to process
            
        Returns:
            List of GitHub repository URLs
            
        Raises:
            ContentExtractionError: If content is invalid or processing fails
        """
        if not content or not isinstance(content, str):
            raise ContentExtractionError("Invalid content provided")
        
        try:
            # Find all GitHub URLs
            matches = self.github_url_pattern.finditer(content)
            
            # Extract and clean URLs
            repos = []
            for match in matches:
                url = match.group(0)
                # Remove trailing slash if present
                if url.endswith('/'):
                    url = url[:-1]
                # Remove hash fragment
                if '#' in url:
                    url = url.split('#')[0]
                repos.append(url)
            
            return repos
            
        except Exception as e:
            logger.error(f"Failed to extract repository links: {str(e)}")
            raise ContentExtractionError(f"Repository extraction failed: {str(e)}")
    
    def collect_metadata(self, repo_url: str) -> Dict:
        """Collect metadata for a repository.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Dictionary containing repository metadata
        """
        return {
            "url": repo_url,
            "first_seen_date": datetime.now(UTC).isoformat(),
            "source_type": "newsletter"
        }
    
    async def process_newsletter_content(
        self,
        email_id: str,
        content: str
    ) -> List[Dict]:
        """Process newsletter content to extract and analyze repositories.
        
        Args:
            email_id: Unique identifier for the newsletter email
            content: Raw newsletter content
            
        Returns:
            List of dictionaries containing repository information and vector IDs
            
        Raises:
            ContentExtractionError: If processing fails
        """
        if not email_id or not content:
            raise ContentExtractionError("Missing required parameters")
        
        try:
            logger.info(f"Processing newsletter content for email {email_id}")
            
            # Extract repository links
            repo_urls = self.extract_repository_links(content)
            if not repo_urls:
                logger.info("No repository links found in content")
                return []
            
            # Process each repository
            results = []
            for url in repo_urls:
                try:
                    # Collect metadata
                    metadata = self.collect_metadata(url)
                    
                    # Store in vector storage
                    vector_id = await self.vector_store.store_repository({
                        "github_url": url,
                        "description": f"Repository found in newsletter {email_id}: {url}",
                        "first_seen_date": metadata["first_seen_date"]
                    })
                    
                    results.append({
                        "url": url,
                        "vector_id": vector_id,
                        "metadata": metadata
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to process repository {url}: {str(e)}")
                    # Continue processing other repositories
                    continue
            
            logger.info(f"Successfully processed {len(results)} repositories")
            return results
            
        except Exception as e:
            logger.error(f"Failed to process newsletter content: {str(e)}")
            raise ContentExtractionError(f"Newsletter processing failed: {str(e)}")
