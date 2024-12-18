"""README Generator agent for maintaining the repository list."""

import json
import logging
import logfire
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ModelRetry

logger = logging.getLogger(__name__)

# Minimum stars threshold for including repositories
MIN_STARS_THRESHOLD = 1000

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

class ValidationResult(BaseModel):
    """Validation result from LLM."""
    is_valid: bool
    issues: List[str] = []
    reasoning: str

class ReadmeGenerator:
    """Agent for generating and updating the repository README."""
    
    def __init__(self, db):
        """Initialize the ReadmeGenerator agent.
        
        Args:
            db: Database connection for fetching repository and topic data
        """
        try:
            self.db = db

            # Initialize validation agent
            self._validation_agent = Agent(
                "openai:gpt-4o",
                result_type=ValidationResult,
                system_prompt=(
                    "You are a specialized validation agent for README content. Your task is to:\n"
                    "1. Analyze the provided markdown content for quality and completeness\n"
                    "2. Check for issues like truncated content, missing sections, or poor formatting\n"
                    "3. Return a structured validation result\n\n"
                    "Focus on these aspects:\n"
                    "- Content completeness (no truncation with '...', 'etc', 'and so on')\n"
                    "- Proper category structure (h2 categories, h3 subcategories)\n"
                    "- Repository entry formatting (links, descriptions, stars, update dates)\n"
                    "- Overall coherence and readability\n"
                    "- Logical organization of content\n"
                    "- No explanatory text or meta-commentary\n\n"
                    "Be thorough in your analysis and provide clear reasoning for any issues found."
                )
            )

            # Initialize main agent for markdown generation
            self._agent = Agent(
                "openai:gpt-4o",
                result_type=str,  # Final result is markdown string
                deps_type=ReadmeContent,
                retries=3,  # Increased retries to allow for self-correction
                system_prompt=(
                    "You are a specialized agent for generating a well-organized markdown README "
                    "listing AI/ML GitHub repositories. Your task is to:\n\n"
                    "1. First call get_category_data() to retrieve the repository and category data\n"
                    "2. Then pass that COMPLETE data object to format_markdown() to format it\n"
                    "3. Finally call validate_content() to ensure the output meets quality standards\n\n"
                    "The markdown should follow these guidelines:\n"
                    "- Use h2 (##) for parent categories\n"
                    "- Use h3 (###) for subcategories\n"
                    "- Format repository entries as bullet points\n"
                    "- Include repository metadata (stars, update date)\n"
                    "- Sort repositories by stars (descending)\n"
                    "- Ensure proper spacing and readability\n"
                    "- NEVER truncate or abbreviate the content\n\n"
                    "IMPORTANT:\n"
                    "- Generate ONLY the categorized list\n"
                    "- NO title (it's in the template)\n"
                    "- NO notes about star thresholds\n"
                    "- NO conclusions or summaries\n"
                    "- NO explanatory text\n"
                    "- ONLY categories and repository entries"
                )
            )

            # Register tools
            self._agent.tool(self.get_category_data)
            self._agent.tool(self.format_markdown)
            self._agent.tool(self.validate_content)

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
            
            # Convert raw repositories to Repository objects and filter by stars
            repositories = []
            for repo_dict in raw_repositories:
                try:
                    repo_data = dict(repo_dict) if hasattr(repo_dict, 'keys') else repo_dict
                    repo = await self._convert_to_repository(repo_data)
                    # Only include repositories with sufficient stars
                    if repo.stars >= MIN_STARS_THRESHOLD:
                        repositories.append(repo)
                    else:
                        logger.debug(f"Skipping repository with insufficient stars: {repo.github_url} ({repo.stars} stars)")
                except ValueError as e:
                    logger.warning(f"Skipping invalid repository: {e}")
                    logfire.warning(
                        "Skipping invalid repository",
                        component="readme_generator",
                        error=str(e),
                        repository=repo_data.get('github_url', 'unknown')
                    )
                    continue

            # Build category structure (only for categories with qualifying repositories)
            category_structure = {}
            for tid, topic in topics.items():
                # Filter repositories for this category
                category_repos = [
                    repo for repo in repositories
                    if any(t["topic_id"] == tid for t in repo.topics)
                ]
                
                # Only include categories that have repositories meeting the star threshold
                if category_repos:
                    category_structure[str(tid)] = CategoryStructure(
                        name=topic["name"],
                        parent_id=topic.get("parent_id"),
                        repositories=category_repos
                    )

            logfire.info(
                "Built category structure",
                component="readme_generator",
                category_count=len(category_structure),
                total_repositories=len(repositories)
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
            if not content.categories:
                raise ModelRetry("No categories provided in content object")

            markdown = []
            
            # Add parent categories first
            parent_categories = {
                tid: cat for tid, cat in content.categories.items() 
                if not cat.parent_id
            }
            
            if not parent_categories:
                raise ModelRetry("No parent categories found in content")
            
            for tid, category in parent_categories.items():
                # Add parent category
                markdown.append(f"\n## {category.name}")
                
                # Add repositories for this category
                if category.repositories:
                    # Sort by stars
                    category.repositories.sort(key=lambda r: r.stars, reverse=True)
                    for repo in category.repositories:
                        name = repo.github_url.split('/')[-1]
                        # Format date to exclude timestamp
                        date = repo.last_updated.split('T')[0] if 'T' in repo.last_updated else repo.last_updated
                        markdown.append(
                            f"\n- [{name}]({repo.github_url}) - {repo.description} "
                            f"⭐ {repo.stars} | Updated: {date}"
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
                            # Format date to exclude timestamp
                            date = repo.last_updated.split('T')[0] if 'T' in repo.last_updated else repo.last_updated
                            markdown.append(
                                f"\n- [{name}]({repo.github_url}) - {repo.description} "
                                f"⭐ {repo.stars} | Updated: {date}"
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
            if isinstance(e, ModelRetry):
                raise
            raise ModelRetry(f"Error formatting markdown: {str(e)}")

    async def validate_content(self, ctx: RunContext[ReadmeContent], markdown: str) -> bool:
        """Validate the generated markdown content using LLM-based analysis.
        
        Args:
            markdown: Generated markdown content to validate
            
        Returns:
            True if content is valid, raises ModelRetry if issues found
            
        Raises:
            ModelRetry: If content has quality issues that need to be fixed
        """
        try:
            # Get validation result from LLM
            result = await self._validation_agent.run(
                f"Please analyze this markdown content for quality and completeness:\n\n{markdown}\n\n"
                "Check for issues like:\n"
                "- Truncated content (e.g. '...', 'etc', 'and so on')\n"
                "- Missing sections\n"
                "- Improper formatting\n"
                "- Meta-commentary or explanatory text\n"
                "- Notes about star thresholds\n"
                "- Conclusions or summaries\n"
                "- Any other quality concerns\n\n"
                "The content should ONLY contain categories and repository entries.",
                deps=None  # Validation agent doesn't need deps
            )
            
            # Log validation result
            logger.info(f"Content validation result: {result.data.is_valid}")
            if result.data.issues:
                logger.info("Validation issues found:\n" + "\n".join(f"- {issue}" for issue in result.data.issues))
            
            logfire.info(
                "Content validation completed",
                component="readme_generator",
                is_valid=result.data.is_valid,
                issues=result.data.issues,
                reasoning=result.data.reasoning
            )
            
            # If validation failed, raise ModelRetry with issues
            if not result.data.is_valid:
                error_msg = (
                    "Content validation failed:\n" +
                    "\n".join(f"- {issue}" for issue in result.data.issues) +
                    f"\n\nReasoning: {result.data.reasoning}"
                )
                raise ModelRetry(error_msg)
            
            return True
            
        except Exception as e:
            if isinstance(e, ModelRetry):
                raise
            logger.error(f"Failed to validate content: {e}")
            logfire.error(
                "Failed to validate content",
                component="readme_generator",
                error=str(e)
            )
            raise ModelRetry(f"Error validating content: {str(e)}")

    def _get_stats(self, content: ReadmeContent) -> Dict[str, str]:
        """Get statistics about the repository list.
        
        Args:
            content: ReadmeContent object with repository data
            
        Returns:
            Dictionary of statistics
        """
        # Count unique repositories (a repo might be in multiple categories)
        unique_repos = set()
        for category in content.categories.values():
            for repo in category.repositories:
                unique_repos.add(repo.github_url)
        
        return {
            "LAST_UPDATED_DATE": datetime.now().strftime("%Y-%m-%d"),
            "TOTAL_REPOS": str(len(unique_repos)),
            "CATEGORY_COUNT": str(len(content.categories))
        }

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
            
            # Generate AI content
            result = await self._agent.run(
                "Generate a well-organized markdown README using the provided category structure. "
                "First call get_category_data() to get the data, then pass that COMPLETE data object "
                "to format_markdown() to format it, and finally call validate_content() to ensure "
                "the output meets quality standards. Generate ONLY the categorized list with "
                "NO title, notes, conclusions, or any other explanatory text.",
                deps=initial_data
            )
            
            # Get template content
            template_path = Path("README.template.md")
            if not template_path.exists():
                raise FileNotFoundError("README.template.md not found")
            template_content = template_path.read_text()
            
            # Get statistics
            stats = self._get_stats(initial_data)
            
            # Replace placeholders
            final_content = template_content.replace("{AI_GENERATED_CONTENT}", result.data)
            for key, value in stats.items():
                final_content = final_content.replace(f"{{{key}}}", value)
            
            logger.info("Successfully generated complete README content")
            logfire.info(
                "Successfully generated complete README content",
                component="readme_generator",
                content_length=len(final_content),
                stats=stats
            )
            return final_content
            
        except Exception as e:
            logger.error(f"Failed to generate markdown: {str(e)}")
            logfire.error(
                "Failed to generate markdown",
                component="readme_generator",
                error=str(e)
            )
            raise
