"""Content extraction and repository summarization agent."""

import re
import logging
import aiohttp
import base64
import json
import yaml
from datetime import datetime, UTC, timedelta
from typing import List, Dict, Optional, Any, Set, Tuple
from pathlib import Path

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext, ModelRetry
from db.connection import Database
from processing.core.newsletter_url_processor import NewsletterUrlProcessor

logger = logging.getLogger(__name__)

class ContentExtractionError(Exception):
    """Raised when content extraction fails."""
    pass

class CategoryValidationError(Exception):
    """Raised when category validation fails."""
    pass

class CategoryRank(BaseModel):
    """Category ranking model."""
    rank: int
    category: str

class NewCategorySuggestion(BaseModel):
    """New category suggestion model."""
    name: str
    parent_category: Optional[str]
    description: str
    example_repos: List[str]
    differentiation: str

class RepositorySummary(BaseModel):
    """Repository summary model."""
    is_genai: bool
    other_category_description: Optional[str]
    primary_purpose: str
    key_technologies: List[str]
    target_users: str
    main_features: List[str]
    technical_domain: str
    ranked_categories: Optional[List[CategoryRank]]
    new_category_suggestion: Optional[NewCategorySuggestion]

class ContentExtractorAgent:
    """Agent responsible for extracting and summarizing GitHub repositories from newsletter content."""
    
    def __init__(self, github_token: str, db: Optional[Database] = None, max_age_hours: float = 0):
        """Initialize the Content Extractor agent.
        
        Args:
            github_token: GitHub API token for repository access
            db: Optional database connection. If None, creates new connection.
            max_age_hours: Maximum age in hours before repository data is refreshed (0 means always refresh)
        """
        self.github_token = github_token
        self.db = db or Database()
        self.max_age_hours = max_age_hours
        self.processed_repos = set()
        
        # Add URL processor
        self.url_processor = NewsletterUrlProcessor(db=self.db)
        
        # Load taxonomy
        taxonomy_path = Path(__file__).parent.parent / "config" / "taxonomy.yaml"
        with open(taxonomy_path) as f:
            self.taxonomy = yaml.safe_load(f)["taxonomy"]
        
        # Build valid category set
        self.valid_categories = set()
        for category, data in self.taxonomy.items():
            self.valid_categories.add(category)
            for subcategory in data["subcategories"]:
                self.valid_categories.add(f"{category}/{subcategory}")
                self.valid_categories.add(subcategory)
        
        # Format taxonomy for prompt
        taxonomy_text = "Current Taxonomy:\n"
        for category, data in self.taxonomy.items():
            taxonomy_text += f"\n{category}\n"
            for subcategory in data["subcategories"]:
                taxonomy_text += f"- {subcategory}\n"
        
        # Agent for repository summarization and categorization
        self.summarization_agent = Agent(
            "openai:gpt-4o-mini",
            result_type=RepositorySummary,
            retries=2,
            system_prompt=(
                "You are a specialized agent for analyzing GitHub repositories in the "
                "Generative AI and Large Language Model (LLM) space. Your task is to:\n\n"
                "1. Determine if a repository is GenAI/LLM-related\n"
                "2. Generate a structured summary of relevant repositories\n"
                "3. Categorize repositories using the provided taxonomy\n"
                "4. Identify potential new categories when needed\n\n"
                f"{taxonomy_text}\n"
                "Instructions:\n\n"
                "1. First, determine if the repository is related to GenAI/LLMs. If not, "
                "mark is_genai as false and provide a brief explanation in other_category_description.\n\n"
                "2. For GenAI/LLM repositories:\n"
                "   - Assign 1-5 categories from the taxonomy above\n"
                "   - Use EXACT category names from taxonomy (including parent category if using subcategory)\n"
                "   - Rank categories by relevance (1 = most relevant)\n"
                "   - Categories can be either top-level or subcategories\n"
                "   - Repository MUST be categorized using existing taxonomy\n\n"
                "3. If you identify a clear need for a new category:\n"
                "   - Still categorize using existing taxonomy\n"
                "   - Provide new category suggestion following these criteria:\n"
                "     * Must be at same hierarchical level as current categories\n"
                "     * For subcategory: Specify parent category\n"
                "     * For top-level: May include optional subcategories\n"
                "     * Must represent a distinct, significant area not covered by existing categories\n"
                "     * Must be clearly the best categorization for this repository"
            )
        )
        
        # Regex for GitHub repository URLs
        self.github_url_pattern = re.compile(
            r'https://github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-_.]+/?(?:#[a-zA-Z0-9-_]*)?'
        )
    
    def validate_categories(self, summary: RepositorySummary) -> List[str]:
        """Validate categories against taxonomy.
        
        Args:
            summary: Repository summary including categories
            
        Returns:
            List of invalid categories found
            
        Raises:
            CategoryValidationError: If validation fails
        """
        if not summary.is_genai:
            return []  # Non-GenAI repos don't need category validation
            
        invalid_categories = []
        if summary.ranked_categories:
            for category_data in summary.ranked_categories:
                if category_data.category not in self.valid_categories:
                    invalid_categories.append(category_data.category)
        
        return invalid_categories
    
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
        metadata: Dict[str, Any],
        invalid_categories: Optional[List[str]] = None
    ) -> RepositorySummary:
        """Generate structured summary of repository using LLM.
        
        Args:
            metadata: Repository metadata including README
            invalid_categories: Optional list of invalid categories from previous attempt
            
        Returns:
            Structured summary following defined format
            
        Raises:
            ContentExtractionError: If summary generation fails
        """
        try:
            # Prepare base prompt
            base_prompt = (
                f"Repository: {metadata['full_name']}\n"
                f"Description: {metadata['description']}\n"
                f"Language: {metadata['language']}\n"
                f"Topics: {', '.join(metadata['topics'])}\n"
                f"Stars: {metadata['stars']}\n"
                f"Forks: {metadata['forks']}\n\n"
                f"README Content:\n{metadata['readme_content']}\n\n"
            )
            
            # Add feedback if there were invalid categories
            if invalid_categories:
                base_prompt += (
                    "\nPrevious attempt used invalid categories:\n"
                    f"{', '.join(invalid_categories)}\n"
                    "Please use EXACT category names from the taxonomy, "
                    "including parent category for subcategories (e.g. 'Model Development/Pretraining').\n\n"
                )
            
            base_prompt += (
                "Based on the repository information and README content above, "
                "determine if this is a GenAI/LLM-related repository and if so, "
                "generate a structured summary with appropriate categorization. "
                "Follow the format and categorization guidelines carefully."
            )
            
            # Call LLM using run method - PydanticAI will handle parsing and validation
            response = await self.summarization_agent.run(base_prompt)
            summary = response.data
            
            # Validate categories against taxonomy
            invalid_cats = self.validate_categories(summary)
            if invalid_cats:
                # Retry once with feedback
                if invalid_categories is None:  # Only retry once
                    logger.info(f"Invalid categories found: {invalid_cats}, retrying...")
                    raise ModelRetry(
                        f"Invalid categories used: {', '.join(invalid_cats)}. "
                        "Please use exact category names from the taxonomy."
                    )
                else:
                    raise CategoryValidationError(
                        f"Invalid categories after retry: {invalid_cats}"
                    )
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate repository summary: {str(e)}")
            if isinstance(e, ModelRetry):
                raise  # Let PydanticAI handle the retry
            raise ContentExtractionError(f"Summary generation failed: {str(e)}")
    
    async def _should_update_repository(self, repo_url: str) -> bool:
        """Check if repository should be updated based on age.
        
        Args:
            repo_url: Repository URL
            
        Returns:
            True if repository should be updated, False otherwise
        """
        try:
            # Query for existing repository
            row = self.db.fetch_one(
                "SELECT first_seen_date FROM repositories WHERE github_url = ?",
                (repo_url,)
            )
            
            # If no results or max_age_hours is 0, should update
            if not row or self.max_age_hours == 0:
                return True
                
            # Parse stored data
            try:
                first_seen = datetime.fromisoformat(row['first_seen_date'])
                age = datetime.now(UTC) - first_seen
                
                return age > timedelta(hours=self.max_age_hours)
                
            except (ValueError, KeyError) as e:
                logger.warning(f"Error parsing stored data, will update: {str(e)}")
                return True
                
        except Exception as e:
            logger.warning(f"Error checking repository age, will update: {str(e)}")
            return True
    
    async def store_repository_data(
        self,
        repo_url: str,
        metadata: Dict[str, Any],
        summary: RepositorySummary,
        source_id: str
    ) -> int:
        """Store repository data and categories in database.
        
        Args:
            repo_url: Repository URL
            metadata: Repository metadata
            summary: Generated summary with categories
            source_id: Source identifier (e.g. newsletter-{email_id})
            
        Returns:
            Repository ID from database
            
        Raises:
            ContentExtractionError: If database operations fail
        """
        try:
            now = datetime.now(UTC)
            
            # Only store GenAI repositories
            if not summary.is_genai:
                logger.info(f"Skipping non-GenAI repository: {repo_url}")
                return 0
            
            # Insert repository
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO repositories (
                        github_url, first_seen_date, last_mentioned_date,
                        mention_count, metadata
                    ) VALUES (?, ?, ?, 1, ?)
                    ON CONFLICT(github_url) DO UPDATE SET
                        last_mentioned_date = ?,
                        mention_count = mention_count + 1,
                        metadata = ?
                    RETURNING id
                    """,
                    (
                        repo_url,
                        now.isoformat(),
                        now.isoformat(),
                        json.dumps({
                            **metadata,
                            "summary": summary.model_dump(),
                            "source_id": source_id
                        }),
                        now.isoformat(),
                        json.dumps({
                            **metadata,
                            "summary": summary.model_dump(),
                            "source_id": source_id
                        })
                    )
                )
                repo_id = cursor.fetchone()[0]
                
                # Store categories
                if summary.ranked_categories:
                    for category in summary.ranked_categories:
                        # First insert/get topic
                        cursor = conn.execute(
                            """
                            INSERT INTO topics (
                                name, first_seen_date, last_seen_date,
                                mention_count
                            ) VALUES (?, ?, ?, 1)
                            ON CONFLICT(name) DO UPDATE SET
                                last_seen_date = ?,
                                mention_count = mention_count + 1
                            RETURNING id
                            """,
                            (
                                category.category,
                                now.isoformat(),
                                now.isoformat(),
                                now.isoformat()
                            )
                        )
                        topic_id = cursor.fetchone()[0]
                        
                        # Check if relationship exists
                        cursor = conn.execute(
                            """
                            SELECT id FROM repository_categories 
                            WHERE repository_id = ? AND topic_id = ?
                            """,
                            (repo_id, topic_id)
                        )
                        existing = cursor.fetchone()
                        
                        if existing:
                            # Update existing relationship
                            conn.execute(
                                """
                                UPDATE repository_categories 
                                SET confidence_score = ?
                                WHERE repository_id = ? AND topic_id = ?
                                """,
                                (
                                    1.0 / category.rank,  # Convert rank to confidence score
                                    repo_id,
                                    topic_id
                                )
                            )
                        else:
                            # Insert new relationship
                            conn.execute(
                                """
                                INSERT INTO repository_categories (
                                    repository_id, topic_id, confidence_score
                                ) VALUES (?, ?, ?)
                                """,
                                (
                                    repo_id,
                                    topic_id,
                                    1.0 / category.rank  # Convert rank to confidence score
                                )
                            )
            
            return repo_id
            
        except Exception as e:
            logger.error(f"Failed to store repository data: {str(e)}")
            raise ContentExtractionError(f"Database storage failed: {str(e)}")
    
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
            List of dictionaries containing repository information
            
        Raises:
            ContentExtractionError: If processing fails
        """
        if not email_id or not content:
            raise ContentExtractionError("Missing required parameters")
        
        try:
            logger.info(f"Processing newsletter content for email {email_id}")
            
            # Get newsletter ID
            newsletter = self.db.fetch_one(
                "SELECT id FROM newsletters WHERE email_id = ?",
                (email_id,)
            )
            if not newsletter:
                raise ContentExtractionError(f"Newsletter not found: {email_id}")
            
            newsletter_id = newsletter['id']
            
            # Extract repository links from newsletter content
            repo_urls = set(self.extract_repository_links(content))
            logger.info(f"Found {len(repo_urls)} GitHub repositories in newsletter content")
            
            # Extract and process other URLs
            all_urls = self.url_processor.url_fetcher.extract_urls(content)
            other_urls = [url for url in all_urls if url not in repo_urls]
            
            # Process other URLs in parallel and extract GitHub links from their content
            url_tasks = []
            for url in other_urls:
                url_tasks.append(
                    self.url_processor.fetch_and_cache_url_content(url, newsletter_id)
                )
            
            # Wait for all URL processing tasks to complete
            url_results = []
            url_contents = await asyncio.gather(*url_tasks, return_exceptions=True)
            for url, result in zip(other_urls, url_contents):
                if isinstance(result, Exception):
                    logger.error(f"Failed to process URL {url}: {str(result)}")
                    continue
                    
                if result:
                    # Store URL content result
                    url_results.append({
                        "url": url,
                        "content": result
                    })
                    
                    # Extract GitHub links from URL content
                    content_repo_urls = set(self.extract_repository_links(result))
                    if content_repo_urls:
                        logger.info(
                            f"Found {len(content_repo_urls)} GitHub repositories in content from {url}"
                        )
                        repo_urls.update(content_repo_urls)
            
            # Process repositories in parallel
            repo_tasks = []
            for url in repo_urls:
                # Skip if already processed
                if url in self.processed_repos:
                    logger.info(f"Skipping already processed repository: {url}")
                    continue
                
                # Check if repository needs updating
                if not await self._should_update_repository(url):
                    logger.info(f"Skipping up-to-date repository: {url}")
                    continue
                
                repo_tasks.append(self._process_single_repository(url, email_id))
            
            # Wait for all repository processing tasks to complete
            repo_results = []
            results = await asyncio.gather(*repo_tasks, return_exceptions=True)
            for url, result in zip(
                [task._args[0] for task in repo_tasks],  # Get URLs from task args
                results
            ):
                if isinstance(result, Exception):
                    logger.error(f"Failed to process repository {url}: {str(result)}")
                    continue
                if result:
                    repo_results.append(result)
                    self.processed_repos.add(url)
            
            logger.info(
                f"Successfully processed {len(repo_results)} repositories "
                f"({len(repo_urls - set(r['url'] for r in repo_results))} failed) "
                f"and {len(url_results)} other URLs"
            )
            
            return [{
                "repositories": repo_results,
                "urls": url_results
            }]
            
        except Exception as e:
            logger.error(f"Failed to process newsletter content: {str(e)}")
            raise ContentExtractionError(f"Newsletter processing failed: {str(e)}")
    
    async def _process_single_repository(
        self,
        url: str,
        email_id: str
    ) -> Optional[Dict]:
        """Process a single repository URL.
        
        Args:
            url: Repository URL to process
            email_id: Newsletter email ID for source tracking
            
        Returns:
            Dictionary containing repository information or None if processing fails
        """
        try:
            # Fetch metadata and README
            metadata = await self.fetch_repository_metadata(url)
            
            # Generate structured summary with categories
            summary = await self.generate_repository_summary(metadata)
            
            # Store in database if GenAI-related
            repo_id = 0
            if summary.is_genai:
                repo_id = await self.store_repository_data(
                    url,
                    metadata,
                    summary,
                    f"newsletter-{email_id}"
                )
            
            return {
                "url": url,
                "repository_id": repo_id,
                "summary": summary.model_dump(),
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to process repository {url}: {str(e)}")
            raise
