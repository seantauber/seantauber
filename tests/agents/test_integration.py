"""Integration tests for the complete README updating system."""

import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel

from processing.embedchain_store import EmbedchainStore
from agents.orchestrator import AgentOrchestrator, OrchestratorDeps
from agents.newsletter_monitor import NewsletterMonitor
from agents.content_extractor import ContentExtractorAgent
from agents.topic_analyzer import TopicAnalyzer
from agents.repository_curator import RepositoryCurator
from agents.readme_generator import ReadmeGenerator

pytestmark = pytest.mark.asyncio

class TestReadmeSystemIntegration:
    """Integration test suite for the complete README updating system."""

    @pytest.fixture
    def mock_embedchain_store(self):
        """Create mock EmbedchainStore with vector operations."""
        store = AsyncMock(spec=EmbedchainStore)
        
        # Mock vector operations
        store.store_repository = AsyncMock(return_value="vec123")
        store.query_repositories = AsyncMock(return_value=[
            {"id": "vec123", "score": 0.95, "metadata": {"github_url": "https://github.com/test/repo"}}
        ])
        
        return store

    @pytest.fixture
    def mock_newsletter_data(self):
        """Sample newsletter data for testing."""
        return {
            'email_id': 'news123',
            'content': (
                'Check out these awesome AI projects:\n'
                'https://github.com/test/ml-project - A machine learning framework\n'
                'https://github.com/test/nlp-tool - Natural language processing library'
            ),
            'metadata': {
                'subject': 'AI Weekly Newsletter',
                'date': '2024-01-15'
            }
        }

    @pytest.fixture
    def mock_repository_data(self):
        """Sample repository data for testing."""
        return {
            'github_url': 'https://github.com/test/ml-project',
            'description': 'A machine learning framework',
            'stars': 1000,
            'last_updated': '2024-01-15',
            'topics': ['machine-learning', 'ai'],
            'vector_id': 'vec123',
            'first_seen_date': datetime.now(UTC).isoformat()
        }

    @pytest.fixture
    def integrated_pipeline(self, mock_embedchain_store, mock_newsletter_data, mock_repository_data):
        """Create integrated pipeline with real agents and mock storage."""
        
        # Configure newsletter monitor
        newsletter_monitor = AsyncMock(spec=NewsletterMonitor)
        newsletter_monitor.process_newsletters.return_value = [mock_newsletter_data]
        
        # Configure content extractor with vector storage
        content_extractor = AsyncMock(spec=ContentExtractorAgent)
        content_extractor.process_newsletter_content.return_value = [{
            'github_url': mock_repository_data['github_url'],
            'vector_id': mock_repository_data['vector_id'],
            'metadata': {
                'first_seen_date': datetime.now(UTC).isoformat(),
                'source_type': 'newsletter'
            }
        }]
        
        # Configure topic analyzer with vector storage
        topic_analyzer = AsyncMock(spec=TopicAnalyzer)
        topic_analyzer.analyze_repository_topics.return_value = [
            {'topic_id': 1, 'confidence_score': 0.9},
            {'topic_id': 2, 'confidence_score': 0.8}
        ]
        
        # Configure repository curator with vector storage
        repository_curator = AsyncMock(spec=RepositoryCurator)
        
        # Create a real RepositoryCurator instance for some methods
        real_curator = RepositoryCurator(mock_embedchain_store)
        
        async def process_repository(repo):
            # First check for duplicates using real implementation
            await real_curator.detect_duplicate(repo)
            
            # Then store the repository
            await mock_embedchain_store.store_repository({
                'description': repo.get('description', ''),
                'github_url': repo['github_url'],
                'first_seen_date': repo.get('metadata', {}).get('first_seen_date')
            })
            return mock_repository_data
            
        repository_curator.process_repository.side_effect = process_repository
        repository_curator.detect_duplicate.side_effect = real_curator.detect_duplicate
        
        # Configure readme generator
        readme_generator = AsyncMock(spec=ReadmeGenerator)
        readme_generator.update_github_readme.return_value = True
        
        # Create orchestrator with all components
        orchestrator = AgentOrchestrator(
            embedchain_store=mock_embedchain_store,
            newsletter_monitor=newsletter_monitor,
            content_extractor=content_extractor,
            topic_analyzer=topic_analyzer,
            repository_curator=repository_curator,
            readme_generator=readme_generator
        )
        
        # Initialize pipeline stats
        orchestrator.error_count = 0
        
        return orchestrator

    async def test_complete_pipeline_flow(self, integrated_pipeline, mock_newsletter_data, mock_repository_data):
        """Test complete data flow through the pipeline."""
        # Run the complete pipeline
        result = await integrated_pipeline.run_pipeline()
        
        # Verify pipeline completed successfully
        assert result is True
        
        # Verify each stage was called with correct data
        integrated_pipeline.newsletter_monitor.process_newsletters.assert_called_once()
        
        # Verify content extraction
        content_extractor_call = integrated_pipeline.content_extractor.process_newsletter_content.call_args
        assert content_extractor_call is not None
        email_id = content_extractor_call[0][0]
        content = content_extractor_call[0][1]
        assert email_id == mock_newsletter_data['email_id']
        assert content == mock_newsletter_data['content']
        
        # Verify topic analysis
        topic_analyzer_call = integrated_pipeline.topic_analyzer.analyze_repository_topics.call_args
        assert topic_analyzer_call is not None
        repo_arg = topic_analyzer_call[0][0]
        assert repo_arg['github_url'] == mock_repository_data['github_url']
        
        # Verify repository curation
        curator_call = integrated_pipeline.repository_curator.process_repository.call_args
        assert curator_call is not None
        repo_arg = curator_call[0][0]
        assert repo_arg['github_url'] == mock_repository_data['github_url']
        assert 'topics' in repo_arg
        
        # Verify README generation
        readme_call = integrated_pipeline.readme_generator.update_github_readme.call_args
        assert readme_call is not None

    async def test_vector_storage_integration(self, integrated_pipeline, mock_embedchain_store):
        """Test vector storage operations throughout pipeline."""
        # Run pipeline
        result = await integrated_pipeline.run_pipeline()
        assert result is True
        
        # Verify vector storage operations
        mock_embedchain_store.store_repository.assert_called()  # Should be called for storing content
        mock_embedchain_store.query_repositories.assert_called()  # Should be called for similarity checks
        
        # Verify vector IDs are properly passed between stages
        curator_call = integrated_pipeline.repository_curator.process_repository.call_args
        assert curator_call is not None
        repo_arg = curator_call[0][0]
        assert 'vector_id' in repo_arg  # Repository should have vector ID after processing

    async def test_error_handling_and_recovery(self, integrated_pipeline, mock_embedchain_store):
        """Test error handling and recovery mechanisms."""
        # Make newsletter monitor fail on first attempt
        integrated_pipeline.newsletter_monitor.process_newsletters.side_effect = [
            Exception("Temporary error"),
            [{'email_id': 'news123', 'content': 'Test content'}]
        ]
        
        # Run pipeline with retry
        result = await integrated_pipeline.run_pipeline(max_retries=2)
        
        # Verify pipeline recovered and completed
        assert result is True
        assert integrated_pipeline.newsletter_monitor.process_newsletters.call_count == 2
        
        # Verify error was logged but recovered
        assert integrated_pipeline.error_count == 0  # Should be 0 since pipeline recovered
        
        # Verify pipeline stats were updated
        stats = integrated_pipeline.get_pipeline_stats()
        assert stats['last_run'] is not None
        assert stats['processed_count'] > 0

    async def test_empty_stage_handling(self, integrated_pipeline):
        """Test handling of empty results at various pipeline stages."""
        # Make newsletter monitor return empty list
        integrated_pipeline.newsletter_monitor.process_newsletters.return_value = []
        
        # Run pipeline
        result = await integrated_pipeline.run_pipeline()
        
        # Verify pipeline handled empty result correctly
        assert result is True
        
        # Verify subsequent stages weren't called
        integrated_pipeline.content_extractor.process_newsletter_content.assert_not_called()
        integrated_pipeline.topic_analyzer.analyze_repository_topics.assert_not_called()
        integrated_pipeline.repository_curator.process_repository.assert_not_called()
        integrated_pipeline.readme_generator.update_github_readme.assert_not_called()

    async def test_data_validation_between_stages(self, integrated_pipeline, mock_repository_data):
        """Test data validation and transformation between pipeline stages."""
        # Make content extractor return invalid data
        integrated_pipeline.content_extractor.process_newsletter_content.return_value = [{
            'github_url': '',  # Invalid URL
            'vector_id': 'vec123',
            'metadata': {'first_seen_date': datetime.now(UTC).isoformat()}
        }]
        
        # Make topic analyzer raise exception for invalid data
        integrated_pipeline.topic_analyzer.analyze_repository_topics.side_effect = ValueError("Invalid repository URL")
        
        # Run pipeline and verify it handles invalid data appropriately
        with pytest.raises(Exception, match="Pipeline failed at repository analysis"):
            await integrated_pipeline.run_pipeline()
        
        # Verify pipeline stats reflect the error
        stats = integrated_pipeline.get_pipeline_stats()
        assert stats['error_count'] > 0

    async def test_concurrent_vector_operations(self, integrated_pipeline, mock_embedchain_store):
        """Test handling of concurrent vector storage operations."""
        # Mock multiple repositories being processed
        integrated_pipeline.content_extractor.process_newsletter_content.return_value = [
            {
                'github_url': f'https://github.com/test/repo-{i}',
                'vector_id': f'vec{i}',
                'metadata': {
                    'first_seen_date': datetime.now(UTC).isoformat(),
                    'source_type': 'newsletter'
                }
            }
            for i in range(3)
        ]
        
        # Run pipeline
        result = await integrated_pipeline.run_pipeline()
        assert result is True
        
        # Verify vector operations were called for each repository
        assert mock_embedchain_store.store_repository.call_count >= 3  # Should be called for each repo
        assert mock_embedchain_store.query_repositories.call_count >= 3  # Should check for duplicates
