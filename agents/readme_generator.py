"""README Generator agent for maintaining the repository list."""

import json
import logging
import logfire
from datetime import datetime
from typing import Dict, List, Optional

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
    
    def __init__(self, db):
        """Initialize the ReadmeGenerator agent.
        
        Args:
            db: Database connection for fetching repository and topic data
        """
        try:
            self.db = db

            # Initialize agent for markdown generation
            self._agent = Agent(
                "openai:gpt-4o",
                result_type=str,  # Final result is markdown string
                deps_type=ReadmeContent,
                retries=2,
                system_prompt=(
                    "You are a specialized agent for generating a well-organized markdown README "
                    "listing AI/ML GitHub repositories. Your task is to:\n\n"
                    "1. First call get_category_data() to retrieve the repository and category data\n"
                    "2. Then call format_markdown() with the retrieved data to generate the final markdown\n\n"
                    "The markdown should follow these guidelines:\n"
                    "- Use h1 (#) for main title\n"
                    "- Use h2 (##) for parent categories\n"
                    "- Use h3 (###) for subcategories\n"
                    "- Format repository entries as bullet points\n"
                    "- Include repository metadata (stars, update date)\n"
                    "- Sort repositories by stars (descending)\n"
                    "- Ensure proper spacing and readability"
                )
            )

            # Register tools
            self._agent.tool(self.get_category_data)
            self._agent.tool(self.format_markdown)

            logger.info("ReadmeGenerator agent initialized successfully")
            logfire.info("ReadmeGenerator agent initialized", component="readme_generator")
        except Exception as e:
            logger.error(f"Failed to initialize ReadmeGenerator agent: {str(e)}")
            logfire.error(
                "Failed to initialize ReadmeGenerator agent",
                component="readme_generator",
                error=str(e)
            )
            raise

    @property
    def agent(self):
        """Get the underlying agent instance."""
        return self._agent

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
            logfire.error(
                "Missing required field in repository data",
                component="readme_generator",
                error=str(e),
                repository=repo_dict.get('github_url', 'unknown')
            )
            raise ValueError(f"Missing required field: {e}")
        except Exception as e:
            logger.error(f"Failed to convert repository data: {e}")
            logfire.error(
                "Failed to convert repository data",
                component="readme_generator",
                error=str(e),
                repository=repo_dict.get('github_url', 'unknown')
            )
            raise ValueError(f"Invalid repository data: {e}")

    async def get_category_data(self, ctx: RunContext[ReadmeContent]) -> ReadmeContent:
        """Get categorized repository data.
        
        Returns:
            ReadmeContent object with categorized repositories
        """
        try:
            # Get repositories and topics
            raw_repositories = await self.db.get_repositories()
            topics = await self.db.get_topics()
            
            logger.debug(f"Retrieved {len(raw_repositories)} repositories and {len(topics)} topics")
            logfire.info(
                "Retrieved repository and topic data",
                component="readme_generator",
                repository_count=len(raw_repositories),
                topic_count=len(topics)
            )
            
            # Convert raw repositories to Repository objects
            repositories = []
            for repo_dict in raw_repositories:
                try:
                    repo_data = dict(repo_dict) if hasattr(repo_dict, 'keys') else repo_dict
                    repo = await self._convert_to_repository(repo_data)
                    repositories.append(repo)
                except ValueError as e:
                    logger.warning(f"Skipping invalid repository: {e}")
                    logfire.warning(
                        "Skipping invalid repository",
                        component="readme_generator",
                        error=str(e),
                        repository=repo_data.get('github_url', 'unknown')
                    )
                    continue

            # Build category structure
            category_structure = {}
            for tid, topic in topics.items():
                category_structure[str(tid)] = CategoryStructure(
                    name=topic["name"],
                    parent_id=topic.get("parent_id"),
                    repositories=[
                        repo for repo in repositories
                        if any(t["topic_id"] == tid for t in repo.topics)
                    ]
                )

            logfire.info(
                "Built category structure",
                component="readme_generator",
                category_count=len(category_structure)
            )
            return ReadmeContent(categories=category_structure)
        except Exception as e:
            logger.error(f"Failed to get category data: {e}")
            logfire.error(
                "Failed to get category data",
                component="readme_generator",
                error=str(e)
            )
            raise ModelRetry(f"Error getting category data: {str(e)}")

    async def format_markdown(self, ctx: RunContext[ReadmeContent], content: ReadmeContent) -> str:
        """Format the README content as markdown.
        
        Args:
            content: ReadmeContent object with categorized repositories
            
        Returns:
            Formatted markdown string
        """
        try:
            # Format markdown
            markdown = [f"# {content.title}\n"]
            
            # Add parent categories first
            parent_categories = {
                tid: cat for tid, cat in content.categories.items() 
                if not cat.parent_id
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

            logfire.info(
                "Generated markdown content",
                component="readme_generator",
                parent_categories=len(parent_categories),
                total_categories=len(content.categories)
            )
            return "\n".join(markdown)
        except Exception as e:
            logger.error(f"Failed to format markdown: {e}")
            logfire.error(
                "Failed to format markdown",
                component="readme_generator",
                error=str(e)
            )
            raise ModelRetry(f"Error formatting markdown: {str(e)}")

    async def generate_markdown(self) -> str:
        """Generate markdown content for README.
        
        Returns:
            Generated markdown content
            
        Raises:
            Exception: If generation fails
        """
        try:
            # Get initial data
            initial_data = await self.get_category_data(ctx=None)
            
            # Generate content using agent
            result = await self._agent.run(
                "Generate a well-organized markdown README using the provided category structure. "
                "First call get_category_data() to get the data, then call format_markdown() to format it.",
                deps=initial_data
            )
            
            logger.info("Successfully generated markdown content")
            logfire.info(
                "Successfully generated markdown content",
                component="readme_generator",
                content_length=len(result.data)
            )
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to generate markdown: {str(e)}")
            logfire.error(
                "Failed to generate markdown",
                component="readme_generator",
                error=str(e)
            )
            raise
