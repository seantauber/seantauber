"""Agent Orchestrator for coordinating the processing pipeline."""

import logging
from datetime import datetime, UTC
from typing import Dict, List, Optional, Union, Any
from unittest.mock import AsyncMock
from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent, RunContext

from processing.embedchain_store import EmbedchainStore
from agents.newsletter_monitor import NewsletterMonitor, Newsletter
from agents.content_extractor import ContentExtractorAgent
from agents.topic_analyzer import TopicAnalyzer
from agents.repository_curator import RepositoryCurator
from agents.readme_generator import ReadmeGenerator

logger = logging.getLogger(__name__)

class OrchestratorDeps(BaseModel):
    """Dependencies for the orchestrator agent."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    store: Union[EmbedchainStore, AsyncMock]
    newsletter_monitor: Union[NewsletterMonitor, AsyncMock]
    content_extractor: Union[ContentExtractorAgent, AsyncMock]
    topic_analyzer: Union[TopicAnalyzer, AsyncMock]
    repository_curator: Union[RepositoryCurator, AsyncMock]
    readme_generator: Union[ReadmeGenerator, AsyncMock]

class AgentOrchestrator:
    """Orchestrates the processing pipeline between different components."""

    def __init__(
        self,
        embedchain_store: EmbedchainStore,
        newsletter_monitor: NewsletterMonitor,
        content_extractor: ContentExtractorAgent,
        topic_analyzer: TopicAnalyzer,
        repository_curator: RepositoryCurator,
        readme_generator: ReadmeGenerator
    ):
        """
        Initialize Agent Orchestrator.

        Args:
            embedchain_store: Vector storage instance
            newsletter_monitor: Newsletter monitoring component
            content_extractor: Content extraction agent
            topic_analyzer: Topic analysis agent
            repository_curator: Repository curation agent
            readme_generator: README generation agent
        """
        try:
            self._agent = Agent(
                'openai:gpt-4',
                deps_type=OrchestratorDeps,
                result_type=bool,
                system_prompt=(
                    'Coordinate the processing pipeline for GitHub repository curation. '
                    'Monitor the flow of data between components and ensure proper error handling. '
                    'Skip subsequent stages if no data is available to process.'
                )
            )

            self.store = embedchain_store
            self.newsletter_monitor = newsletter_monitor
            self.content_extractor = content_extractor
            self.topic_analyzer = topic_analyzer
            self.repository_curator = repository_curator
            self.readme_generator = readme_generator

            # Pipeline state tracking
            self.last_run: Optional[datetime] = None
            self.processed_count: int = 0
            self.error_count: int = 0

            # Register tools
            self._agent.tool(self.process_newsletters)
            self._agent.tool(self.extract_repositories)
            self._agent.tool(self.analyze_repositories)
            self._agent.tool(self.curate_repositories)
            self._agent.tool(self.generate_readme)

            logger.info("Initialized Agent Orchestrator")
        except Exception as e:
            logger.error(f"Failed to initialize Agent Orchestrator: {str(e)}")
            raise

    @property
    def deps(self) -> OrchestratorDeps:
        """Get agent dependencies."""
        return OrchestratorDeps(
            store=self.store,
            newsletter_monitor=self.newsletter_monitor,
            content_extractor=self.content_extractor,
            topic_analyzer=self.topic_analyzer,
            repository_curator=self.repository_curator,
            readme_generator=self.readme_generator
        )

    async def process_newsletters(
        self,
        ctx: RunContext[OrchestratorDeps],
        max_retries: int = 1
    ) -> List[Newsletter]:
        """
        Process newsletters using the newsletter monitor.

        Args:
            ctx: Run context with dependencies
            max_retries: Maximum number of retry attempts

        Returns:
            List of processed newsletters

        Raises:
            Exception: If processing fails after retries
        """
        attempt = 0
        while attempt <= max_retries:
            try:
                logger.info("Processing newsletters")
                result = await ctx.deps.newsletter_monitor.run()
                newsletters = result.newsletters
                logger.info(f"Processed {len(newsletters)} newsletters")
                return newsletters
            except Exception as e:
                attempt += 1
                if attempt > max_retries:
                    self.error_count += 1
                    logger.error(f"Newsletter processing failed after {max_retries} attempts")
                    raise Exception("Pipeline failed at newsletter processing") from e
                logger.warning(f"Retrying newsletter processing (attempt {attempt})")
        return []

    async def extract_repositories(
        self,
        ctx: RunContext[OrchestratorDeps],
        newsletters: List[Newsletter]
    ) -> List[Dict]:
        """
        Extract repositories from newsletters.

        Args:
            ctx: Run context with dependencies
            newsletters: List of processed newsletters

        Returns:
            List of extracted repositories
        """
        if not newsletters:
            logger.info("No newsletters to process, skipping repository extraction")
            return []

        try:
            logger.info("Extracting repositories from newsletters")
            repositories = await ctx.deps.content_extractor.process_newsletter_content(
                newsletters[0].email_id,  # Access as attribute
                newsletters[0].content    # Access as attribute
            )
            logger.info(f"Extracted {len(repositories)} repositories")
            return repositories
        except Exception as e:
            self.error_count += 1
            logger.error("Repository extraction failed")
            raise Exception("Pipeline failed at repository extraction") from e

    async def analyze_repositories(
        self,
        ctx: RunContext[OrchestratorDeps],
        repositories: List[Dict]
    ) -> List[Dict]:
        """
        Analyze repositories for topics.

        Args:
            ctx: Run context with dependencies
            repositories: List of repositories to analyze

        Returns:
            List of analyzed repositories with topics
        """
        if not repositories:
            logger.info("No repositories to analyze, skipping topic analysis")
            return []

        try:
            logger.info("Analyzing repository topics")
            analyzed_repos = []
            for repo in repositories:
                if not repo.get('github_url'):
                    self.error_count += 1
                    logger.error("Invalid repository data: missing github_url")
                    raise ValueError("Invalid repository URL")
                
                topics = await ctx.deps.topic_analyzer.analyze_repository_topics(repo)
                analyzed = {**repo, 'topics': topics}
                analyzed_repos.append(analyzed)
            logger.info(f"Analyzed {len(analyzed_repos)} repositories")
            return analyzed_repos
        except Exception as e:
            self.error_count += 1
            logger.error("Repository analysis failed")
            raise Exception("Pipeline failed at repository analysis") from e

    async def curate_repositories(
        self,
        ctx: RunContext[OrchestratorDeps],
        repositories: List[Dict]
    ) -> List[Dict]:
        """
        Curate repositories with metadata and vector storage.

        Args:
            ctx: Run context with dependencies
            repositories: List of repositories to curate

        Returns:
            List of curated repositories
        """
        if not repositories:
            logger.info("No repositories to curate, skipping curation")
            return []

        try:
            logger.info("Curating repositories")
            curated_repos = []
            for repo in repositories:
                # Ensure repository has required fields
                if not repo.get('github_url'):
                    logger.warning("Repository missing github_url, skipping")
                    continue
                
                curated = await ctx.deps.repository_curator.process_repository(repo)
                curated_repos.append(curated)
            logger.info(f"Curated {len(curated_repos)} repositories")
            return curated_repos
        except Exception as e:
            self.error_count += 1
            logger.error("Repository curation failed")
            raise Exception("Pipeline failed at repository curation") from e

    async def generate_readme(
        self,
        ctx: RunContext[OrchestratorDeps],
        repositories: List[Dict]
    ) -> bool:
        """
        Generate README with curated repositories.

        Args:
            ctx: Run context with dependencies
            repositories: List of curated repositories

        Returns:
            True if README generation succeeded
        """
        if not repositories:
            logger.info("No repositories to include in README, skipping generation")
            return True

        try:
            logger.info("Generating README")
            success = await ctx.deps.readme_generator.update_github_readme()
            if success:
                logger.info("README generation completed successfully")
            else:
                logger.warning("README generation completed with warnings")
            return success
        except Exception as e:
            self.error_count += 1
            logger.error("README generation failed")
            raise Exception("Pipeline failed at README generation") from e

    async def run_pipeline(self, max_retries: int = 1) -> bool:
        """
        Run the complete processing pipeline.

        Args:
            max_retries: Maximum number of retry attempts for each stage

        Returns:
            True if pipeline completed successfully

        Raises:
            Exception: If any stage of the pipeline fails
        """
        try:
            logger.info("Starting processing pipeline")
            self.last_run = datetime.now(UTC)
            self.processed_count = 0
            self.error_count = 0

            # Create run context with retry count
            ctx = RunContext(deps=self.deps, retry=0)

            # Process newsletters
            newsletters = await self.process_newsletters(ctx, max_retries)
            if not newsletters:
                logger.info("No newsletters to process, ending pipeline early")
                return True

            # Extract repositories
            repositories = await self.extract_repositories(ctx, newsletters)
            if not repositories:
                logger.info("No repositories extracted, ending pipeline early")
                return True

            # Analyze repositories
            analyzed_repos = await self.analyze_repositories(ctx, repositories)
            if not analyzed_repos:
                logger.info("No repositories to analyze, ending pipeline early")
                return True

            # Curate repositories
            curated_repos = await self.curate_repositories(ctx, analyzed_repos)
            if not curated_repos:
                logger.info("No repositories to curate, ending pipeline early")
                return True

            # Generate README
            await self.generate_readme(ctx, curated_repos)

            # Update pipeline stats
            self.processed_count = len(curated_repos)
            logger.info(
                f"Pipeline completed successfully. Processed {self.processed_count} repositories"
            )
            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise

    def get_pipeline_stats(self) -> Dict:
        """
        Get current pipeline statistics.

        Returns:
            Dictionary containing pipeline statistics
        """
        return {
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'processed_count': self.processed_count,
            'error_count': self.error_count
        }
