"""Content extraction and repository summarization agent."""

import re
import logging
import aiohttp
import base64
from datetime import datetime, UTC
from typing import List, Dict, Optional, Any

from pydantic_ai import Agent, RunContext
from processing.embedchain_store import EmbedchainStore

logger = logging.getLogger(__name__)

class ContentExtractionError(Exception):
    """Raised when content extraction fails."""
    pass

class ContentExtractorAgent:
    """Agent responsible for extracting and summarizing GitHub repositories from newsletter content."""
    
    def __init__(self, vector_store: EmbedchainStore, github_token: str):
        """Initialize the Content Extractor agent.
        
        Args:
            vector_store: Vector storage instance for content analysis
            github_token: GitHub API token for repository access
        """
        self.vector_store = vector_store
        self.github_token = github_token
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
        
        # Agent for repository summarization
        self.summarization_agent = Agent(
            "openai:gpt-4",
            system_prompt=(
                "Generate structured summaries of GitHub repositories based on their "
                "README content and metadata. Focus on capturing the repository's "
                "primary purpose, key technologies, target users, main features, "
                "and technical domain."
            )
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
    
    async def fetch_repository_metadata(self, repo_url: str) -> Dict[str, Any]:
        """Fetch repository metadata from GitHub API.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Dictionary containing repository metadata
            
        Raises:
            ContentExtractionError: If API request fails
        """
        try:
            # Extract owner and repo from URL
            _, _, _, owner, repo = repo_url.rstrip('/').split('/')
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            async with aiohttp.ClientSession() as session:
                # Fetch repository metadata
                async with session.get(
                    f'https://api.github.com/repos/{owner}/{repo}',
                    headers=headers
                ) as response:
                    if response.status != 200:
                        raise ContentExtractionError(
                            f"GitHub API error: {response.status}"
                        )
                    repo_data = await response.json()
                
                # Fetch README content
                async with session.get(
                    f'https://api.github.com/repos/{owner}/{repo}/readme',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        readme_data = await response.json()
                        readme_content = base64.b64decode(
                            readme_data['content']
                        ).decode('utf-8')
                    else:
                        readme_content = ""
                        logger.warning(f"README not found for {repo_url}")
            
            return {
                "name": repo_data['name'],
                "full_name": repo_data['full_name'],
                "description": repo_data['description'] or "",
                "stars": repo_data['stargazers_count'],
                "forks": repo_data['forks_count'],
                "language": repo_data['language'],
                "topics": repo_data['topics'],
                "readme_content": readme_content,
                "created_at": repo_data['created_at'],
                "updated_at": repo_data['updated_at']
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch repository metadata: {str(e)}")
            raise ContentExtractionError(f"Metadata fetch failed: {str(e)}")
    
    async def generate_repository_summary(
        self,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured summary of repository using LLM.
        
        Args:
            metadata: Repository metadata including README
            
        Returns:
            Structured summary following defined format
            
        Raises:
            ContentExtractionError: If summary generation fails
        """
        try:
            # Prepare context for LLM
            context = (
                f"Repository: {metadata['full_name']}\n"
                f"Description: {metadata['description']}\n"
                f"Language: {metadata['language']}\n"
                f"Topics: {', '.join(metadata['topics'])}\n"
                f"Stars: {metadata['stars']}\n"
                f"Forks: {metadata['forks']}\n\n"
                f"README Content:\n{metadata['readme_content']}"
            )
            
            # Generate summary using LLM
            prompt = (
                "Based on the repository information and README content, generate a "
                "structured summary with the following format:\n"
                "{\n"
                '    "primary_purpose": "Main goal or function",\n'
                '    "key_technologies": ["tech1", "tech2"],\n'
                '    "target_users": "Primary audience",\n'
                '    "main_features": ["feature1", "feature2"],\n'
                '    "technical_domain": "Specific technical area"\n'
                "}\n\n"
                "Ensure the summary is concise but comprehensive."
            )
            
            response = await self.summarization_agent.complete(
                prompt,
                context=context
            )
            
            # Parse and validate summary
            summary = eval(response.content)  # Safe since we control the LLM output format
            required_fields = [
                "primary_purpose", "key_technologies", "target_users",
                "main_features", "technical_domain"
            ]
            if not all(field in summary for field in required_fields):
                raise ContentExtractionError("Invalid summary format")
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate repository summary: {str(e)}")
            raise ContentExtractionError(f"Summary generation failed: {str(e)}")
    
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
                    # Fetch metadata and README
                    metadata = await self.fetch_repository_metadata(url)
                    
                    # Generate structured summary
                    summary = await self.generate_repository_summary(metadata)
                    
                    # Prepare repository data
                    repo_data = {
                        "github_url": url,
                        "name": metadata["name"],
                        "description": metadata["description"],
                        "summary": summary,
                        "metadata": {
                            "stars": metadata["stars"],
                            "forks": metadata["forks"],
                            "language": metadata["language"],
                            "topics": metadata["topics"],
                            "created_at": metadata["created_at"],
                            "updated_at": metadata["updated_at"]
                        },
                        "first_seen_date": datetime.now(UTC).isoformat(),
                        "source_type": "newsletter",
                        "source_id": email_id
                    }
                    
                    # Store in vector storage
                    vector_id = await self.vector_store.store_repository(repo_data)
                    
                    results.append({
                        "url": url,
                        "vector_id": vector_id,
                        "summary": summary,
                        "metadata": repo_data["metadata"]
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
    
    async def migrate_existing_repositories(self) -> None:
        """Migrate existing repositories to include summaries.
        
        This method fetches all existing repositories from vector storage,
        generates summaries for them, and updates their records.
        
        Raises:
            ContentExtractionError: If migration fails
        """
        try:
            logger.info("Starting repository migration")
            
            # Query all existing repositories
            repositories = await self.vector_store.query_repositories(
                "type:repository",
                limit=1000  # Adjust based on expected repository count
            )
            
            migrated_count = 0
            for repo in repositories:
                try:
                    # Extract URL from stored data
                    repo_url = repo['metadata']['github_url']
                    
                    # Fetch current metadata and README
                    metadata = await self.fetch_repository_metadata(repo_url)
                    
                    # Generate new summary
                    summary = await self.generate_repository_summary(metadata)
                    
                    # Update repository data
                    repo_data = {
                        "github_url": repo_url,
                        "name": metadata["name"],
                        "description": metadata["description"],
                        "summary": summary,
                        "metadata": {
                            "stars": metadata["stars"],
                            "forks": metadata["forks"],
                            "language": metadata["language"],
                            "topics": metadata["topics"],
                            "created_at": metadata["created_at"],
                            "updated_at": metadata["updated_at"]
                        },
                        "first_seen_date": repo['metadata'].get('first_seen_date'),
                        "source_type": repo['metadata'].get('source_type'),
                        "source_id": repo['metadata'].get('source_id')
                    }
                    
                    # Store updated data
                    await self.vector_store.store_repository(repo_data)
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(
                        f"Failed to migrate repository {repo.get('github_url', 'unknown')}: {str(e)}"
                    )
                    continue
            
            logger.info(f"Successfully migrated {migrated_count} repositories")
            
        except Exception as e:
            logger.error(f"Repository migration failed: {str(e)}")
            raise ContentExtractionError(f"Migration failed: {str(e)}")
