"""README Generator agent for maintaining the repository list."""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ModelRetry

logger = logging.getLogger(__name__)

class Repository(BaseModel):
    """Repository data model."""
    github_url: str
    description: str
    topics: List[Dict[str, float]]
    stars: int = 0
    last_updated: str = ""

class Topic(BaseModel):
    """Topic data model."""
    name: str
    parent_id: Optional[int] = None

class CategoryStructure(BaseModel):
    """Category structure with repositories."""
    name: str
    parent_id: Optional[int] = None
    repositories: List[Repository] = []

class ReadmeContent(BaseModel):
    """Structured README content."""
    title: str = "AI/ML GitHub Repository List"
    categories: Dict[str, CategoryStructure]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class ReadmeGenerator:
    """Agent for generating and updating the repository README."""
    
    def __init__(self, db, github_client):
        """Initialize the ReadmeGenerator agent.
        
        Args:
            db: Database connection
            github_client: GitHub client for README updates
        """
        try:
            # Initialize agent for markdown generation
            self._agent = Agent(
                "openai:gpt-4",
                result_type=ReadmeContent,
                retries=2,
                system_prompt=(
                    "You are a specialized agent for generating a well-organized markdown README "
                    "listing AI/ML GitHub repositories. Your task is to:\n\n"
                    "1. Organize repositories by their categories\n"
                    "2. Format each repository entry with description, stars, and update date\n"
                    "3. Ensure proper markdown hierarchy with categories and subcategories\n"
                    "4. Generate clean, consistent formatting\n\n"
                    "Guidelines:\n"
                    "- Use h1 (#) for main title\n"
                    "- Use h2 (##) for parent categories\n"
                    "- Use h3 (###) for subcategories\n"
                    "- Format repository entries as bullet points\n"
                    "- Include repository metadata (stars, update date)\n"
                    "- Sort repositories by stars (descending)\n"
                    "- Ensure proper spacing and readability"
                )
            )
            self.db = db
            self.github = github_client

            logger.info("ReadmeGenerator agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ReadmeGenerator agent: {str(e)}")
            raise

    async def _convert_to_repository(self, repo_dict: Dict) -> Repository:
        """Convert a dictionary to a Repository model.
        
        Args:
            repo_dict: Dictionary containing repository data
            
        Returns:
            Repository model instance
            
        Raises:
            ValueError: If required fields are missing
        """
        try:
            # Convert topics from database format to expected format
            topics = repo_dict.get('topics', [])
            if isinstance(topics, str):
                # Handle case where topics might be stored as JSON string
                import json
                topics = json.loads(topics)
            
            # Extract metadata from JSON if needed
            metadata = repo_dict.get('metadata', {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            
            return Repository(
                github_url=repo_dict['github_url'],
                description=metadata.get('description', repo_dict.get('description', '')),
                topics=topics,
                stars=metadata.get('stars', repo_dict.get('stars', 0)),
                last_updated=metadata.get('updated_at', repo_dict.get('last_updated', ''))
            )
        except KeyError as e:
            logger.error(f"Missing required field in repository data: {e}")
            raise ValueError(f"Missing required field: {e}")
        except Exception as e:
            logger.error(f"Failed to convert repository data: {e}")
            raise ValueError(f"Invalid repository data: {e}")

    async def generate_markdown(self) -> str:
        """Generate markdown content for README.
        
        Returns:
            Generated markdown content
            
        Raises:
            Exception: If generation fails
        """
        try:
            # Get repositories and topics
            raw_repositories = await self.db.get_repositories()
            topics = await self.db.get_topics()
            
            logger.debug(f"Retrieved {len(raw_repositories)} repositories and {len(topics)} topics")
            
            # Convert raw repositories to Repository objects
            repositories = []
            for repo_dict in raw_repositories:
                try:
                    repo_data = dict(repo_dict) if hasattr(repo_dict, 'keys') else repo_dict
                    repo = await self._convert_to_repository(repo_data)
                    repositories.append(repo)
                except ValueError as e:
                    logger.warning(f"Skipping invalid repository: {e}")
                    continue

            # Build category structure
            category_structure = {}
            for tid, topic in topics.items():
                category_structure[str(tid)] = CategoryStructure(
                    name=topic["name"],
                    parent_id=topic["parent_id"],
                    repositories=[
                        repo for repo in repositories
                        if any(t["topic_id"] == tid for t in repo.topics)
                    ]
                )

            # Generate markdown using agent
            result = await self._agent.run(
                "Generate a well-organized markdown README using the provided category structure.",
                deps=ReadmeContent(categories=category_structure)
            )
            content = result.data

            # Format markdown
            markdown = [f"# {content.title}\n"]
            
            # Add parent categories first
            parent_categories = {
                tid: cat for tid, cat in content.categories.items() 
                if cat.parent_id is None
            }
            
            for tid, category in parent_categories.items():
                # Add parent category
                markdown.append(f"\n## {category.name}")
                
                # Add repositories for this category
                if category.repositories:
                    # Sort by stars
                    category.repositories.sort(key=lambda r: r.stars, reverse=True)
                    for repo in category.repositories:
                        name = repo.github_url.split('/')[-1]
                        markdown.append(
                            f"\n- [{name}]({repo.github_url}) - {repo.description} "
                            f"⭐ {repo.stars} | Updated: {repo.last_updated}"
                        )
                else:
                    markdown.append("\nNo repositories in this category.")
                
                # Add child categories
                child_categories = {
                    tid: cat for tid, cat in content.categories.items()
                    if cat.parent_id == tid
                }
                
                for child_tid, child in child_categories.items():
                    markdown.append(f"\n### {child.name}")
                    
                    if child.repositories:
                        # Sort by stars
                        child.repositories.sort(key=lambda r: r.stars, reverse=True)
                        for repo in child.repositories:
                            name = repo.github_url.split('/')[-1]
                            markdown.append(
                                f"\n- [{name}]({repo.github_url}) - {repo.description} "
                                f"⭐ {repo.stars} | Updated: {repo.last_updated}"
                            )
                    else:
                        markdown.append("\nNo repositories in this category.")
            
            logger.info("Successfully generated markdown content")
            return "\n".join(markdown)
            
        except Exception as e:
            logger.error(f"Failed to generate markdown: {str(e)}")
            raise

    async def update_github_readme(self) -> bool:
        """Generate and update the GitHub README.
        
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Generate new markdown content
            markdown = await self.generate_markdown()
            
            # Update GitHub README
            success = await self.github.update_readme(markdown)
            
            if success:
                logger.info("Successfully updated GitHub README")
            else:
                logger.warning("GitHub README update returned False")
            
            return success
        except Exception as e:
            logger.error(f"Failed to update README: {str(e)}")
            return False
