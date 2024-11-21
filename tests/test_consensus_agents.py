"""Tests for the consensus-based categorization system"""
import pytest
from models.repo_models import RepoDetails
from models.curation_models import CategoryHierarchy, EnhancedCurationDetails
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

def test_validation_agent(sample_repo):
    agent = ValidationAgent()
    categories = [
        CategoryHierarchy(
            main_category="AI/ML",
            subcategory="Deep Learning",
            confidence=0.9,
            reasoning="Reviewed categorization"
        )
    ]
    historical_data = {}  # Mock historical data
    
    validated = agent.execute(sample_repo, categories, historical_data)
    
    assert len(validated) == len(categories)
    assert all(isinstance(cat, CategoryHierarchy) for cat in validated)
    assert all(0 <= cat.confidence <= 1.0 for cat in validated)
    assert all(cat.reasoning for cat in validated)

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
    
    result = manager.get_consensus(sample_repo)
    
    assert isinstance(result, EnhancedCurationDetails)
    assert len(result.categories) > 0
    assert result.consensus_data is not None
    assert "agent_decisions" in result.consensus_data
    assert all(
        agent in result.consensus_data["agent_decisions"]
        for agent in ["category_agent", "review_agent", "validation_agent"]
    )
    assert 0 <= result.popularity_score <= 1.0
    assert 0 <= result.trending_score <= 1.0

def test_consensus_manager_end_to_end(sample_repo):
    """Test the complete consensus workflow"""
    manager = ConsensusManager()
    
    # Get consensus categorization
    result = manager.get_consensus(sample_repo)
    
    # Verify the structure and content of the result
    assert isinstance(result, EnhancedCurationDetails)
    assert len(result.categories) > 0
    assert result.consensus_data is not None
    
    # Verify agent decisions are present
    decisions = result.consensus_data["agent_decisions"]
    assert "category_agent" in decisions
    assert "review_agent" in decisions
    assert "validation_agent" in decisions
    
    # Verify confidence scores
    assert all(
        0 <= decisions[agent]["confidence"] <= 1.0
        for agent in ["category_agent", "review_agent", "validation_agent"]
    )
    
    # Verify categories are properly structured
    for category in result.categories:
        assert isinstance(category, CategoryHierarchy)
        assert category.main_category
        assert 0 <= category.confidence <= 1.0
        assert category.reasoning
