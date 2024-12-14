"""Tests for the Repository Curator agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agents.repository_curator import RepositoryCurator
from processing.embedchain_store import EmbedchainStore

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_embedchain_store():
    """Create mock embedchain store."""
    store = AsyncMock(spec=EmbedchainStore)
    # Mock query_repositories for similarity checks with low similarity score
    store.query_repositories = AsyncMock(return_value=[
        {
            'text': 'A different framework',
            'metadata': {'github_url': 'https://github.com/other/framework'},
            'score': 0.3  # Low similarity score to avoid duplicate detection
        }
    ])
    # Mock add_repository to return a vector_id
    store.add_repository = AsyncMock(return_value="test_vector_123")
    return store

@pytest.fixture
def repository_curator(mock_embedchain_store):
    """Create RepositoryCurator instance with mock store."""
    return RepositoryCurator(mock_embedchain_store)

class TestRepositoryCurator:
    """Test suite for RepositoryCurator."""

    async def test_process_repository(self, repository_curator, mock_embedchain_store):
        """Test repository processing."""
        repository = {
            'github_url': 'https://github.com/org/ml-framework',
            'description': 'A machine learning framework',
            'metadata': {
                'stars': 1000,
                'last_updated': '2024-01-15'
            }
        }

        # Debug: Verify mock is configured correctly
        assert mock_embedchain_store.add_repository.return_value == "test_vector_123"

        # Debug: Verify initial query_repositories mock
        similar_repos = await mock_embedchain_store.query_repositories(
            query=repository['description']
        )
        print(f"Initial similarity check results: {similar_repos}")
        assert similar_repos[0]['score'] < repository_curator.DUPLICATE_THRESHOLD

        result = await repository_curator.process_repository(repository)
        
        # Debug: Verify mock was called
        mock_embedchain_store.add_repository.assert_called_once()
        
        # Debug: Print actual result
        print(f"Result from process_repository: {result}")

        assert isinstance(result, dict)
        assert 'github_url' in result
        assert 'vector_id' in result
        assert result['vector_id'] == "test_vector_123"
        assert result['metadata'].get('stars') == 1000

    async def test_detect_duplicate(self, repository_curator):
        """Test duplicate repository detection."""
        repository = {
            'github_url': 'https://github.com/org/ml-framework',
            'description': 'A machine learning framework'
        }

        # Test with similar repository
        repository_curator.store.query_repositories = AsyncMock(return_value=[
            {
                'text': 'A very similar machine learning framework',
                'metadata': {'github_url': 'https://github.com/other/ml-framework'},
                'score': 0.95
            }
        ])

        is_duplicate = await repository_curator.detect_duplicate(repository)
        assert is_duplicate is True

        # Test with non-duplicate
        repository_curator.store.query_repositories = AsyncMock(return_value=[
            {
                'text': 'A completely different project',
                'metadata': {'github_url': 'https://github.com/other/different'},
                'score': 0.2
            }
        ])

        is_duplicate = await repository_curator.detect_duplicate(repository)
        assert is_duplicate is False

    async def test_invalid_repository_handling(self, repository_curator):
        """Test handling of invalid repository data."""
        invalid_repository = {
            'github_url': None,
            'description': 'Some description'
        }

        with pytest.raises(ValueError, match="Repository must have a valid GitHub URL"):
            await repository_curator.process_repository(invalid_repository)

    async def test_metadata_enrichment(self, repository_curator):
        """Test repository metadata enrichment."""
        repository = {
            'github_url': 'https://github.com/org/ml-framework',
            'description': 'A machine learning framework',
            'metadata': {'stars': 1000}
        }

        enriched = await repository_curator.enrich_metadata(repository)
        
        assert isinstance(enriched, dict)
        assert 'metadata' in enriched
        assert enriched['metadata'].get('stars') == 1000
        assert 'last_processed' in enriched['metadata']
        assert 'mention_count' in enriched['metadata']

    async def test_similarity_threshold(self, repository_curator):
        """Test similarity threshold for duplicates."""
        repository = {
            'github_url': 'https://github.com/org/ml-framework',
            'description': 'A machine learning framework'
        }

        # Test with borderline similarity
        repository_curator.store.query_repositories = AsyncMock(return_value=[
            {
                'text': 'Similar but not quite duplicate',
                'metadata': {'github_url': 'https://github.com/other/framework'},
                'score': repository_curator.DUPLICATE_THRESHOLD - 0.01
            }
        ])

        is_duplicate = await repository_curator.detect_duplicate(repository)
        assert is_duplicate is False

        # Test with exact duplicate
        repository_curator.store.query_repositories = AsyncMock(return_value=[
            {
                'text': 'Exact same framework',
                'metadata': {'github_url': 'https://github.com/org/ml-framework'},
                'score': 1.0
            }
        ])

        is_duplicate = await repository_curator.detect_duplicate(repository)
        assert is_duplicate is True
