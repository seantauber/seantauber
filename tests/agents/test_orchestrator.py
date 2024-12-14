"""Tests for the Agent Orchestrator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel
from agents.orchestrator import AgentOrchestrator
from processing.embedchain_store import EmbedchainStore

class TestAgentOrchestrator:
    @pytest.fixture
    def embedchain_store(self):
        """Create a mock EmbedchainStore instance."""
        return AsyncMock(spec=EmbedchainStore)

    @pytest.fixture
    def newsletter_monitor(self):
        """Create a mock NewsletterMonitor instance."""
        mock = AsyncMock()
        mock.process_newsletters = AsyncMock(return_value=[{
            'email_id': 'test123',
            'content': 'Test newsletter content',
            'vector_id': 'vec123'
        }])
        return mock

    @pytest.fixture
    def content_extractor(self):
        """Create a mock ContentExtractor instance."""
        mock = AsyncMock()
        mock.extract_repositories = AsyncMock(return_value=[{
            'github_url': 'https://github.com/test/repo',
            'description': 'Test repository'
        }])
        return mock

    @pytest.fixture
    def topic_analyzer(self):
        """Create a mock TopicAnalyzer instance."""
        mock = AsyncMock()
        mock.analyze_repository = AsyncMock(return_value={
            'github_url': 'https://github.com/test/repo',
            'topics': ['AI', 'Machine Learning']
        })
        return mock

    @pytest.fixture
    def repository_curator(self):
        """Create a mock RepositoryCurator instance."""
        mock = AsyncMock()
        mock.process_repository = AsyncMock(return_value={
            'github_url': 'https://github.com/test/repo',
            'vector_id': 'vec456',
            'metadata': {'topics': ['AI', 'Machine Learning']}
        })
        return mock

    @pytest.fixture
    def readme_generator(self):
        """Create a mock ReadmeGenerator instance."""
        mock = AsyncMock()
        mock.generate_readme = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def orchestrator(
        self,
        embedchain_store,
        newsletter_monitor,
        content_extractor,
        topic_analyzer,
        repository_curator,
        readme_generator
    ):
        """Create an AgentOrchestrator instance with mock agents."""
        return AgentOrchestrator(
            embedchain_store=embedchain_store,
            newsletter_monitor=newsletter_monitor,
            content_extractor=content_extractor,
            topic_analyzer=topic_analyzer,
            repository_curator=repository_curator,
            readme_generator=readme_generator
        )

    @pytest.mark.asyncio
    async def test_process_pipeline(self, orchestrator):
        """Test the full processing pipeline."""
        # Run the pipeline
        result = await orchestrator.run_pipeline()

        # Verify each agent was called in order
        orchestrator.newsletter_monitor.process_newsletters.assert_called_once()
        orchestrator.content_extractor.extract_repositories.assert_called_once()
        orchestrator.topic_analyzer.analyze_repository.assert_called_once()
        orchestrator.repository_curator.process_repository.assert_called_once()
        orchestrator.readme_generator.generate_readme.assert_called_once()

        assert result is True

    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self, orchestrator):
        """Test error handling in the pipeline."""
        # Make newsletter monitor raise an error
        orchestrator.newsletter_monitor.process_newsletters.side_effect = Exception("Test error")

        # Run pipeline and verify error is handled
        with pytest.raises(Exception, match="Pipeline failed at newsletter processing"):
            await orchestrator.run_pipeline()

    @pytest.mark.asyncio
    async def test_pipeline_empty_newsletters(self, orchestrator):
        """Test pipeline behavior with no newsletters."""
        # Return empty list from newsletter monitor
        orchestrator.newsletter_monitor.process_newsletters.return_value = []

        # Run pipeline
        result = await orchestrator.run_pipeline()

        # Verify content extractor wasn't called
        orchestrator.content_extractor.extract_repositories.assert_not_called()
        assert result is True

    @pytest.mark.asyncio
    async def test_pipeline_empty_repositories(self, orchestrator):
        """Test pipeline behavior with no repositories."""
        # Return empty list from content extractor
        orchestrator.content_extractor.extract_repositories.return_value = []

        # Run pipeline
        result = await orchestrator.run_pipeline()

        # Verify topic analyzer wasn't called
        orchestrator.topic_analyzer.analyze_repository.assert_not_called()
        assert result is True

    @pytest.mark.asyncio
    async def test_pipeline_state_tracking(self, orchestrator):
        """Test pipeline state tracking."""
        # Run pipeline
        await orchestrator.run_pipeline()

        # Verify state was tracked
        assert orchestrator.last_run is not None
        assert orchestrator.processed_count > 0

    @pytest.mark.asyncio
    async def test_pipeline_retry_mechanism(self, orchestrator):
        """Test pipeline retry mechanism."""
        # Make first attempt fail, second succeed
        orchestrator.newsletter_monitor.process_newsletters.side_effect = [
            Exception("Temporary error"),
            [{
                'email_id': 'test123',
                'content': 'Test newsletter content',
                'vector_id': 'vec123'
            }]
        ]

        # Run pipeline with retry
        result = await orchestrator.run_pipeline(max_retries=2)

        # Verify retry succeeded
        assert orchestrator.newsletter_monitor.process_newsletters.call_count == 2
        assert result is True
