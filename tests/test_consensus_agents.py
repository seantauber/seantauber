"""Tests for the consensus-based categorization system"""
import pytest
from datetime import datetime, timedelta
from models.repo_models import RepoDetails
from models.curation_models import (
    CategoryHierarchy,
    EnhancedCurationDetails,
    HistoricalDecision,
    RepositoryHistory
)
from agents.consensus_agents import (
    CategoryAgent,
    ReviewAgent,
    ValidationAgent,
    SynthesisAgent,
    ConsensusManager
)

@pytest.fixture
def sample_repo():
    """Sample repository details for testing"""
    return RepoDetails(
        id="test-repo-123",  # Added id field for historical tracking
        name="test-repo",
        full_name="test-org/test-repo",
        description="A deep learning framework for testing",
        html_url="https://github.com/test-org/test-repo",
        topics=["machine-learning", "deep-learning", "python"],
        stargazers_count=1000,
        forks_count=100,
        open_issues_count=50,
        watchers_count=1000,
        language="Python",
        updated_at="2024-01-01T00:00:00Z",
        created_at="2023-01-01T00:00:00Z",
        default_branch="main",
        star_growth_rate=0.5,
        activity_level="high",
        relevance="high"
    )

@pytest.fixture
def sample_historical_data():
    """Sample historical data for testing"""
    history = RepositoryHistory(repository_id="test-repo-123")
    
    # Add some historical decisions
    categories = [
        CategoryHierarchy(
            main_category="AI/ML",
            subcategory="Deep Learning",
            confidence=0.9,
            reasoning="Historical decision 1"
        )
    ]
    
    # Add decisions from different times
    for days_ago in [30, 20, 10]:
        decision = HistoricalDecision(
            timestamp=datetime.utcnow() - timedelta(days=days_ago),
            categories=categories,
            agent_decisions={
                "category_agent": {"confidence": 0.9},
                "review_agent": {"confidence": 0.95},
                "validation_agent": {"confidence": 0.92}
            },
            version="1.0.0",
            metadata={
                "repo_updated_at": "2024-01-01T00:00:00Z",
                "stars": 1000,
                "forks": 100
            }
        )
        history.add_decision(decision)
    
    return history

def test_category_agent(sample_repo):
    agent = CategoryAgent()
    categories = agent.execute(sample_repo)
    
    assert len(categories) > 0
    assert all(isinstance(cat, CategoryHierarchy) for cat in categories)
    assert all(0 <= cat.confidence <= 1.0 for cat in categories)
    assert all(cat.reasoning for cat in categories)

def test_review_agent(sample_repo):
    agent = ReviewAgent()
    initial_categories = [
        CategoryHierarchy(
            main_category="AI/ML",
            subcategory="Deep Learning",
            confidence=0.9,
            reasoning="Initial categorization"
        )
    ]
    
    reviewed = agent.execute(sample_repo, initial_categories)
    
    assert len(reviewed) == len(initial_categories)
    assert all(isinstance(cat, CategoryHierarchy) for cat in reviewed)
    assert all(0 <= cat.confidence <= 1.0 for cat in reviewed)
    assert all(cat.reasoning for cat in reviewed)

def test_validation_agent_with_history(sample_repo, sample_historical_data):
    agent = ValidationAgent()
    categories = [
        CategoryHierarchy(
            main_category="AI/ML",
            subcategory="Deep Learning",
            confidence=0.9,
            reasoning="Reviewed categorization"
        )
    ]
    
    validated = agent.execute(sample_repo, categories, sample_historical_data)
    
    assert len(validated) == len(categories)
    assert all(isinstance(cat, CategoryHierarchy) for cat in validated)
    assert all(0 <= cat.confidence <= 1.0 for cat in validated)
    assert all(cat.reasoning for cat in validated)
    assert all("stability" in cat.reasoning for cat in validated)

def test_validation_agent_category_shift(sample_repo, sample_historical_data):
    agent = ValidationAgent()
    # Test with a different category than historical data
    categories = [
        CategoryHierarchy(
            main_category="Web Dev",  # Different from historical AI/ML
            subcategory="Frontend",
            confidence=0.9,
            reasoning="New categorization"
        )
    ]
    
    validated = agent.execute(sample_repo, categories, sample_historical_data)
    
    assert len(validated) == len(categories)
    assert all("Category shift" in cat.reasoning for cat in validated)
    assert all(cat.confidence < 0.9 for cat in validated)  # Confidence should be reduced

def test_validation_agent_no_history(sample_repo):
    agent = ValidationAgent()
    categories = [
        CategoryHierarchy(
            main_category="AI/ML",
            subcategory="Deep Learning",
            confidence=0.9,
            reasoning="Initial categorization"
        )
    ]
    empty_history = RepositoryHistory(repository_id="test-repo-123")
    
    validated = agent.execute(sample_repo, categories, empty_history)
    
    assert len(validated) == len(categories)
    assert all(cat.confidence == 0.9 for cat in validated)  # Confidence unchanged

def test_synthesis_agent(sample_repo):
    agent = SynthesisAgent()
    categories = [
        CategoryHierarchy(
            main_category="AI/ML",
            subcategory="Deep Learning",
            confidence=0.9,
            reasoning="Validated categorization"
        )
    ]
    agent_decisions = {
        "category_agent": {"confidence": 0.9},
        "review_agent": {"confidence": 0.95},
        "validation_agent": {"confidence": 0.92}
    }
    
    result = agent.execute(sample_repo, categories, agent_decisions)
    
    assert isinstance(result, EnhancedCurationDetails)
    assert len(result.categories) == len(categories)
    assert result.consensus_data is not None
    assert "agent_decisions" in result.consensus_data
    assert 0 <= result.popularity_score <= 1.0
    assert 0 <= result.trending_score <= 1.0

def test_consensus_manager(sample_repo):
    manager = ConsensusManager()
    
    # First categorization
    result1 = manager.get_consensus(sample_repo)
    assert isinstance(result1, EnhancedCurationDetails)
    
    # Second categorization - should use historical data
    result2 = manager.get_consensus(sample_repo)
    assert isinstance(result2, EnhancedCurationDetails)
    
    # Verify historical data was recorded
    assert sample_repo.id in manager.historical_data
    history = manager.historical_data[sample_repo.id]
    assert len(history.decisions) == 2
    assert history.latest_decision is not None
    assert history.statistics is not None
    assert "category_stability" in history.statistics

def test_repository_history():
    history = RepositoryHistory(repository_id="test-repo-123")
    
    # Add a decision
    decision = HistoricalDecision(
        categories=[
            CategoryHierarchy(
                main_category="AI/ML",
                subcategory="Deep Learning",
                confidence=0.9,
                reasoning="Test decision"
            )
        ],
        agent_decisions={
            "category_agent": {"confidence": 0.9},
            "review_agent": {"confidence": 0.95},
            "validation_agent": {"confidence": 0.92}
        },
        version="1.0.0"
    )
    
    history.add_decision(decision)
    
    assert len(history.decisions) == 1
    assert history.latest_decision == decision
    assert history.statistics is not None
    assert "category_stability" in history.statistics
    assert "confidence_trends" in history.statistics
    assert "total_decisions" in history.statistics

def test_consensus_manager_end_to_end(sample_repo):
    """Test the complete consensus workflow with historical tracking"""
    manager = ConsensusManager()
    
    # First categorization
    result1 = manager.get_consensus(sample_repo)
    assert isinstance(result1, EnhancedCurationDetails)
    
    # Verify historical data was recorded
    assert sample_repo.id in manager.historical_data
    history = manager.historical_data[sample_repo.id]
    assert len(history.decisions) == 1
    
    # Second categorization
    result2 = manager.get_consensus(sample_repo)
    assert isinstance(result2, EnhancedCurationDetails)
    assert len(history.decisions) == 2
    
    # Verify historical tracking
    assert history.latest_decision is not None
    assert history.statistics is not None
    assert "category_stability" in history.statistics
    assert "confidence_trends" in history.statistics
    
    # Verify agent decisions are tracked
    for result in [result1, result2]:
        decisions = result.consensus_data["agent_decisions"]
        assert "category_agent" in decisions
        assert "review_agent" in decisions
        assert "validation_agent" in decisions
        assert all(
            0 <= decisions[agent]["confidence"] <= 1.0
            for agent in ["category_agent", "review_agent", "validation_agent"]
        )
