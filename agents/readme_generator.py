"""README Generator agent for maintaining the repository list."""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

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

class DatabaseDeps(BaseModel):
    """Database dependencies."""
    get_repositories: callable
    get_topics: callable

class GitHubDeps(BaseModel):
    """GitHub client dependencies."""
    update_readme: callable

class ReadmeGeneratorDeps(BaseModel):
    """Combined dependencies for ReadmeGenerator."""
    db: DatabaseDeps
    github: GitHubDeps

class ReadmeGenerator:
    """Agent for generating and updating the repository README."""
    
    def __init__(self, db, github_client):
        """Initialize the ReadmeGenerator agent."""
        try:
            self._agent = Agent(
                "openai:gpt-4",
                deps_type=ReadmeGeneratorDeps,
                result_type=bool,
                system_prompt=(
                    "Generate a well-organized markdown README listing AI/ML GitHub repositories "
                    "categorized by their topics. Format each repository entry with its description, "
                    "stars, and last update date."
                )
            )
            self.db = db
            self.github = github_client

            # Register tools
            self._agent.tool(self.update_category_structure)
            
            logger.info("ReadmeGenerator agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ReadmeGenerator agent: {str(e)}")
            raise

    @property
    def deps(self) -> ReadmeGeneratorDeps:
        """Get agent dependencies."""
        return ReadmeGeneratorDeps(
            db=DatabaseDeps(
                get_repositories=self.db.get_repositories,
                get_topics=self.db.get_topics
            ),
            github=GitHubDeps(
                update_readme=self.github.update_readme
            )
        )

    async def generate_markdown(self) -> str:
        """Generate markdown content for README."""
        try:
            # Get repositories and topics
            repositories = await self.db.get_repositories()
            topics = await self.db.get_topics()
            
            logger.debug(f"Retrieved {len(repositories)} repositories and {len(topics)} topics")
            
            # Validate repositories
            for repo in repositories:
                if not repo.github_url:
                    logger.error("Found repository with invalid URL")
                    raise ValueError("Invalid repository URL")
            
            # Generate markdown content
            content = ["# AI/ML GitHub Repository List\n"]
            
            if not repositories:
                content.append("\nNo repositories found.")
                return "\n".join(content)
            
            # Organize by parent topics first
            parent_topics = {
                tid: topic for tid, topic in topics.items() 
                if topic['parent_id'] is None
            }
            
            for parent_id, parent_topic in parent_topics.items():
                # Add parent category
                content.append(f"\n## {parent_topic['name']}")
                
                # Add repositories for this category
                parent_repos = [
                    repo for repo in repositories
                    if any(t['topic_id'] == parent_id for t in repo.topics)
                ]
                content.extend(self._format_repositories(parent_repos))
                
                # Add child categories
                child_topics = {
                    tid: topic for tid, topic in topics.items()
                    if topic['parent_id'] == parent_id
                }
                
                for child_id, child_topic in child_topics.items():
                    content.append(f"\n## {child_topic['name']}")
                    
                    # Add repositories for this subcategory
                    child_repos = [
                        repo for repo in repositories
                        if any(t['topic_id'] == child_id for t in repo.topics)
                    ]
                    content.extend(self._format_repositories(child_repos))
            
            logger.info("Successfully generated markdown content")
            return "\n".join(content)
        except Exception as e:
            logger.error(f"Failed to generate markdown: {str(e)}")
            raise

    def _format_repositories(self, repositories: List[Repository]) -> List[str]:
        """Format repository entries as markdown."""
        if not repositories:
            return ["\nNo repositories in this category."]
            
        # Sort by stars (descending)
        repositories.sort(key=lambda r: r.stars, reverse=True)
        
        formatted = []
        for repo in repositories:
            # Extract repo name from URL
            name = repo.github_url.split('/')[-1]
            
            # Format entry with stars and update date
            entry = (
                f"\n- [{name}]({repo.github_url}) - {repo.description} "
                f"⭐ {repo.stars} | Updated: {repo.last_updated}"
            )
            formatted.append(entry)
            
        return formatted

    async def update_category_structure(
        self,
        ctx: RunContext[ReadmeGeneratorDeps]
    ) -> Dict[str, Dict]:
        """Get the current category structure with repositories."""
        try:
            topics = await ctx.deps.db.get_topics()
            repositories = await ctx.deps.db.get_repositories()
            
            structure = {}
            for tid, topic in topics.items():
                structure[tid] = {
                    "name": topic["name"],
                    "parent_id": topic["parent_id"],
                    "repositories": [
                        repo for repo in repositories
                        if any(t["topic_id"] == tid for t in repo.topics)
                    ]
                }
            
            logger.debug(f"Generated category structure with {len(structure)} topics")
            return structure
        except Exception as e:
            logger.error(f"Failed to update category structure: {str(e)}")
            raise

    async def update_github_readme(self) -> bool:
        """Generate and update the GitHub README."""
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

    async def run(self, prompt: str) -> bool:
        """Run the agent with a prompt."""
        try:
            result = await self._agent.run(prompt, deps=self.deps)
            return result.data
        except Exception as e:
            logger.error(f"Agent run failed: {str(e)}")
            raise
