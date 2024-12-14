"""Tests for the Topic Analyzer agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agents.topic_analyzer import TopicAnalyzer
from processing.embedchain_store import EmbedchainStore

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_embedchain_store():
    """Create mock embedchain store."""
    store = AsyncMock(spec=EmbedchainStore)
    store.query_repositories = AsyncMock(return_value=[
        {
            'text': 'A machine learning framework for NLP tasks',
            'metadata': {'github_url': 'https://github.com/org/nlp-ml'},
            'score': 0.85
        }
    ])
    return store

@pytest.fixture
def topic_analyzer(mock_embedchain_store):
    """Create TopicAnalyzer instance with mock store."""
    return TopicAnalyzer(mock_embedchain_store)

class TestTopicAnalyzer:
    """Test suite for TopicAnalyzer."""

    async def test_analyze_repository_topics(self, topic_analyzer):
        """Test repository topic analysis."""
        repository = {
            'github_url': 'https://github.com/org/nlp-ml',
            'description': 'A machine learning framework for NLP tasks'
        }

        topics = await topic_analyzer.analyze_repository_topics(repository)
        
        assert isinstance(topics, list)
        assert len(topics) > 0
        for topic in topics:
            assert 'topic_id' in topic
            assert 'confidence_score' in topic
            assert 0 <= topic['confidence_score'] <= 1

    async def test_get_parent_topics(self, topic_analyzer):
        """Test getting parent topics."""
        # Use NLP topic which has ML as parent
        topic_id = 2  # Natural Language Processing
        
        parent_topics = await topic_analyzer.get_parent_topics(topic_id)
        
        assert isinstance(parent_topics, list)
        assert 1 in parent_topics  # Machine Learning should be parent

    async def test_invalid_repository_handling(self, topic_analyzer):
        """Test handling of invalid repository data."""
        invalid_repository = {
            'github_url': 'https://github.com/org/repo',
            'description': None
        }

        with pytest.raises(ValueError, match="Repository must have a description"):
            await topic_analyzer.analyze_repository_topics(invalid_repository)

    async def test_semantic_similarity_check(self, topic_analyzer):
        """Test semantic similarity calculation."""
        repository = {
            'github_url': 'https://github.com/org/nlp-ml',
            'description': 'A machine learning framework for NLP tasks'
        }

        # Test against ML/NLP category
        similarity = await topic_analyzer._calculate_similarity(
            repository['description'],
            'Machine Learning and Natural Language Processing'
        )
        
        assert isinstance(similarity, float)
        assert 0 <= similarity <= 1
        assert similarity > topic_analyzer.MIN_CONFIDENCE_THRESHOLD

    async def test_fixed_categories_exist(self, topic_analyzer):
        """Test that fixed categories are properly initialized."""
        categories = topic_analyzer.get_fixed_categories()
        
        assert isinstance(categories, dict)
        assert len(categories) > 0
        # Check for some expected root categories
        root_categories = [cat for cat in categories.values() if cat['parent_id'] is None]
        assert len(root_categories) > 0
        # Verify ML and NLP relationship
        assert categories[2]['parent_id'] == 1  # NLP should be child of ML

    async def test_confidence_threshold(self, topic_analyzer):
        """Test confidence threshold filtering."""
        repository = {
            'github_url': 'https://github.com/org/random-repo',
            'description': 'A completely unrelated project'
        }

        # Mock low similarity score
        topic_analyzer.store.query_repositories = AsyncMock(return_value=[
            {'text': 'unrelated', 'score': 0.3}
        ])

        topics = await topic_analyzer.analyze_repository_topics(repository)
        
        # All returned topics should meet minimum confidence threshold
        for topic in topics:
            assert topic['confidence_score'] >= topic_analyzer.MIN_CONFIDENCE_THRESHOLD
