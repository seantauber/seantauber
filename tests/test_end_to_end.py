"""End-to-end tests for the complete GitHub repository curation workflow."""

import os
import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from processing.embedchain_store import EmbedchainStore
from processing.gmail.client import GmailClient
from agents.orchestrator import AgentOrchestrator
from agents.newsletter_monitor import NewsletterMonitor
from agents.content_extractor import ContentExtractorAgent
from agents.topic_analyzer import TopicAnalyzer
from agents.repository_curator import RepositoryCurator
from agents.readme_generator import ReadmeGenerator

pytestmark = pytest.mark.asyncio

class TestEndToEndWorkflow:
    """End-to-end test suite for the complete workflow."""

    @pytest.fixture
    def mock_gmail_client(self):
        """Create mock Gmail client with test data."""
        client = AsyncMock(spec=GmailClient)
        client.get_newsletters.return_value = [{
            'id': 'email123',
            'subject': 'AI Weekly Newsletter',
            'content': (
                'Check out these exciting AI projects:\n\n'
                'https://github.com/test/ml-project - A new machine learning framework\n'
                'Key features:\n'
                '- Fast training\n'
                '- Easy deployment\n'
                '- Extensive documentation\n\n'
                'https://github.com/test/nlp-tool - Advanced NLP library\n'
                'Features:\n'
                '- State-of-the-art models\n'
                '- Multi-language support\n'
                '- Easy integration\n'
            ),
            'date': '2024-01-15'
        }]
        return client

    @pytest.fixture
    def mock_github_client(self):
        """Create mock GitHub client with repository data."""
        client = AsyncMock()
        client.get_repository_info.return_value = {
            'name': 'ml-project',
            'description': 'A new machine learning framework',
            'stars': 1000,
            'last_updated': '2024-01-15',
            'topics': ['machine-learning', 'ai', 'deep-learning'],
            'readme': '# ML Project\n\nFast and easy machine learning framework.'
        }
        client.update_readme.return_value = True
        return client

    @pytest.fixture
    async def test_system(self, mock_gmail_client, mock_github_client, tmp_path):
        """Create complete test system with real components and mock clients."""
        # Set up vector storage with temporary path
        vector_db_path = tmp_path / "vector_store"
        os.makedirs(vector_db_path, exist_ok=True)
        embedchain_store = EmbedchainStore(str(vector_db_path))
        
        # Create agents with real implementations
        newsletter_monitor = NewsletterMonitor(mock_gmail_client, embedchain_store)
        content_extractor = ContentExtractorAgent(embedchain_store)
        topic_analyzer = TopicAnalyzer(embedchain_store)
        repository_curator = RepositoryCurator(embedchain_store)
        readme_generator = ReadmeGenerator(mock_github_client)
        
        # Create orchestrator
        orchestrator = AgentOrchestrator(
            embedchain_store=embedchain_store,
            newsletter_monitor=newsletter_monitor,
            content_extractor=content_extractor,
            topic_analyzer=topic_analyzer,
            repository_curator=repository_curator,
            readme_generator=readme_generator
        )
        
        return {
            'orchestrator': orchestrator,
            'store': embedchain_store,
            'gmail_client': mock_gmail_client,
            'github_client': mock_github_client,
            'vector_db_path': vector_db_path
        }

    async def test_complete_workflow(self, test_system):
        """Test the complete workflow from newsletter processing to README generation."""
        orchestrator = test_system['orchestrator']
        github_client = test_system['github_client']
        store = test_system['store']
        
        # Run complete pipeline
        result = await orchestrator.run_pipeline()
        
        # Verify pipeline completed successfully
        assert result is True
        
        # Verify vector storage contains embedded content
        vector_queries = await store.search(
            "machine learning framework",
            limit=1
        )
        assert len(vector_queries) > 0
        assert vector_queries[0]['score'] > 0.7  # High similarity score
        
        # Verify README was updated
        github_client.update_readme.assert_called_once()
        readme_content = github_client.update_readme.call_args[0][0]
        assert 'ml-project' in readme_content.lower()
        assert 'machine learning' in readme_content.lower()
        
        # Verify pipeline statistics
        stats = orchestrator.get_pipeline_stats()
        assert stats['processed_count'] > 0
        assert stats['error_count'] == 0

    async def test_duplicate_repository_handling(self, test_system):
        """Test handling of duplicate repositories across newsletters."""
        orchestrator = test_system['orchestrator']
        gmail_client = test_system['gmail_client']
        
        # Add duplicate repository in second newsletter
        gmail_client.get_newsletters.return_value.append({
            'id': 'email124',
            'subject': 'Tech Newsletter',
            'content': 'https://github.com/test/ml-project - Another mention of the ML framework',
            'date': '2024-01-16'
        })
        
        # Run pipeline
        result = await orchestrator.run_pipeline()
        
        # Verify pipeline completed successfully
        assert result is True
        
        # Verify only one instance of the repository was processed
        stats = orchestrator.get_pipeline_stats()
        assert stats['processed_count'] == 2  # Should process both repos but detect duplicate
        
        # Verify README contains repository only once
        github_client = test_system['github_client']
        readme_content = github_client.update_readme.call_args[0][0]
        assert readme_content.count('ml-project') == 1

    async def test_incremental_updates(self, test_system):
        """Test incremental updates with new newsletters."""
        orchestrator = test_system['orchestrator']
        gmail_client = test_system['gmail_client']
        
        # First run with initial newsletter
        await orchestrator.run_pipeline()
        initial_count = orchestrator.processed_count
        
        # Add new newsletter
        gmail_client.get_newsletters.return_value = [{
            'id': 'email125',
            'subject': 'New AI Projects',
            'content': 'https://github.com/test/new-project - Brand new AI project',
            'date': '2024-01-17'
        }]
        
        # Second run
        await orchestrator.run_pipeline()
        
        # Verify only new content was processed
        assert orchestrator.processed_count > initial_count
        
        # Verify README includes new repository
        github_client = test_system['github_client']
        readme_content = github_client.update_readme.call_args[0][0]
        assert 'new-project' in readme_content.lower()

    async def test_error_recovery_and_consistency(self, test_system):
        """Test system recovery and data consistency after errors."""
        orchestrator = test_system['orchestrator']
        github_client = test_system['github_client']
        
        # Make GitHub client fail on first attempt
        github_client.update_readme.side_effect = [
            Exception("GitHub API error"),
            True  # Succeed on retry
        ]
        
        # Run pipeline with retry
        result = await orchestrator.run_pipeline(max_retries=2)
        
        # Verify pipeline recovered and completed
        assert result is True
        assert github_client.update_readme.call_count == 2
        
        # Verify data consistency
        stats = orchestrator.get_pipeline_stats()
        assert stats['error_count'] == 0  # Should be 0 since pipeline recovered
        
        # Verify vector storage consistency
        store = test_system['store']
        vectors = await store.search("machine learning", limit=10)
        assert len(vectors) > 0  # Vector storage should be intact

    async def test_system_cleanup(self, test_system):
        """Test proper cleanup of system resources."""
        vector_db_path = test_system['vector_db_path']
        store = test_system['store']
        
        # Run pipeline
        await test_system['orchestrator'].run_pipeline()
        
        # Verify vector storage is properly maintained
        assert os.path.exists(vector_db_path)
        vectors = await store.search("test query", limit=1)
        assert isinstance(vectors, list)
        
        # Clean up
        await store.close()  # Should properly close connections
        
        # Verify storage is in consistent state
        assert os.path.exists(vector_db_path)  # Files should still exist
        assert os.access(vector_db_path, os.R_OK)  # Should be readable
