from datetime import datetime, timedelta
from models.curation_models import (
    CategoryHierarchy,
    CurationDetails,
    EnhancedCurationDetails,
    HistoricalDecision,
    RepositoryHistory
)
import pytest

def test_category_hierarchy_valid():
    category = CategoryHierarchy(
        main_category="AI/ML",
        subcategory="Deep Learning",
        confidence=0.95,
        reasoning="Strong evidence of deep learning frameworks"
    )
    assert category.main_category == "AI/ML"
    assert category.subcategory == "Deep Learning"
    assert category.confidence == 0.95
    assert category.reasoning == "Strong evidence of deep learning frameworks"

def test_category_hierarchy_invalid_confidence():
    with pytest.raises(ValueError):
        CategoryHierarchy(
            main_category="AI/ML",
            confidence=1.5,  # Invalid: > 1.0
            reasoning="Test"
        )

def test_category_hierarchy_missing_reasoning():
    with pytest.raises(ValueError):
        CategoryHierarchy(
            main_category="AI/ML",
            confidence=0.9,
            reasoning=""  # Invalid: empty string
        )

def test_category_hierarchy_optional_subcategory():
    category = CategoryHierarchy(
        main_category="AI/ML",
        confidence=0.95,
        reasoning="Valid without subcategory"
    )
    assert category.subcategory is None

def test_curation_details_valid():
    details = CurationDetails(
        tags=["python", "machine-learning"],
        popularity_score=0.85,
        trending_score=0.75
    )
    assert len(details.tags) == 2
    assert details.popularity_score == 0.85
    assert details.trending_score == 0.75

def test_enhanced_curation_details_valid():
    details = EnhancedCurationDetails(
        tags=["python", "machine-learning"],
        popularity_score=0.85,
        trending_score=0.75,
        categories=[
            CategoryHierarchy(
                main_category="AI/ML",
                confidence=0.95,
                reasoning="Test reasoning"
            )
        ]
    )
    assert len(details.categories) == 1
    assert details.version == "1.0.0"
    assert isinstance(details.consensus_data, dict)

def test_enhanced_curation_details_invalid_version():
    with pytest.raises(ValueError):
        EnhancedCurationDetails(
            tags=["python"],
            popularity_score=0.85,
            trending_score=0.75,
            categories=[
                CategoryHierarchy(
                    main_category="AI/ML",
                    confidence=0.95,
                    reasoning="Test reasoning"
                )
            ],
            version="invalid"  # Invalid version format
        )

def test_enhanced_curation_details_empty_categories():
    with pytest.raises(ValueError):
        EnhancedCurationDetails(
            tags=["python"],
            popularity_score=0.85,
            trending_score=0.75,
            categories=[]  # Invalid: empty list
        )

def test_enhanced_curation_details_defaults():
    details = EnhancedCurationDetails(
        tags=["python"],
        popularity_score=0.85,
        trending_score=0.75,
        categories=[
            CategoryHierarchy(
                main_category="AI/ML",
                confidence=0.95,
                reasoning="Test reasoning"
            )
        ]
    )
    assert details.related_repos == []
    assert details.consensus_data == {}
    assert details.version == "1.0.0"

def test_historical_decision_valid():
    decision = HistoricalDecision(
        categories=[
            CategoryHierarchy(
                main_category="AI/ML",
                confidence=0.95,
                reasoning="Test reasoning"
            )
        ],
        agent_decisions={"test_agent": {"confidence": 0.9}},
        version="1.0.0"
    )
    assert isinstance(decision.timestamp, datetime)
    assert len(decision.categories) == 1
    assert decision.version == "1.0.0"

def test_historical_decision_with_metadata():
    metadata = {"source": "automated", "trigger": "schedule"}
    decision = HistoricalDecision(
        categories=[
            CategoryHierarchy(
                main_category="AI/ML",
                confidence=0.95,
                reasoning="Test reasoning"
            )
        ],
        agent_decisions={"test_agent": {"confidence": 0.9}},
        version="1.0.0",
        metadata=metadata
    )
    assert decision.metadata == metadata

def test_repository_history_initialization():
    history = RepositoryHistory(repository_id="test-repo-123")
    assert history.repository_id == "test-repo-123"
    assert len(history.decisions) == 0
    assert history.latest_decision is None

def test_repository_history_add_decision():
    history = RepositoryHistory(repository_id="test-repo-123")
    decision = HistoricalDecision(
        categories=[
            CategoryHierarchy(
                main_category="AI/ML",
                confidence=0.95,
                reasoning="Test reasoning"
            )
        ],
        agent_decisions={"test_agent": {"confidence": 0.9}},
        version="1.0.0"
    )
    history.add_decision(decision)
    assert len(history.decisions) == 1
    assert history.latest_decision == decision

def test_repository_history_multiple_decisions():
    history = RepositoryHistory(repository_id="test-repo-123")
    # Add decisions with different timestamps
    for days_ago in [30, 20, 10]:
        decision = HistoricalDecision(
            timestamp=datetime.utcnow() - timedelta(days=days_ago),
            categories=[
                CategoryHierarchy(
                    main_category="AI/ML",
                    confidence=0.95,
                    reasoning=f"Decision from {days_ago} days ago"
                )
            ],
            agent_decisions={
                "category_agent": {"confidence": 0.9}
            },
            version="1.0.0"
        )
        history.add_decision(decision)
    assert len(history.decisions) == 3
    assert history.latest_decision.categories[0].reasoning == "Decision from 10 days ago"

def test_repository_history_category_stability():
    history = RepositoryHistory(repository_id="test-repo-123")
    categories = ["AI/ML", "Web", "AI/ML"]  # AI/ML should be more stable
    for i, category in enumerate(categories):
        decision = HistoricalDecision(
            categories=[
                CategoryHierarchy(
                    main_category=category,
                    confidence=0.95,
                    reasoning=f"Decision {i}"
                )
            ],
            agent_decisions={"test_agent": {"confidence": 0.9}},
            version="1.0.0"
        )
        history.add_decision(decision)
    
    assert "AI/ML:None" in history.statistics["category_stability"]
    assert history.statistics["category_stability"]["AI/ML:None"] > history.statistics["category_stability"]["Web:None"]

def test_repository_history_confidence_trends():
    history = RepositoryHistory(repository_id="test-repo-123")
    confidences = [0.8, 0.85, 0.9]  # Increasing confidence trend
    for confidence in confidences:
        decision = HistoricalDecision(
            categories=[
                CategoryHierarchy(
                    main_category="AI/ML",
                    confidence=0.95,
                    reasoning="Test reasoning"
                )
            ],
            agent_decisions={"test_agent": {"confidence": confidence}},
            version="1.0.0"
        )
        history.add_decision(decision)
    
    assert "test_agent" in history.statistics["confidence_trends"]
    assert history.statistics["confidence_trends"]["test_agent"] == sum(confidences) / len(confidences)

def test_repository_history_empty_statistics():
    history = RepositoryHistory(repository_id="test-repo-123")
    history._update_statistics()  # Should handle empty decisions list
    assert history.statistics["total_decisions"] == 0
    assert history.statistics["category_stability"] == {}
    assert history.statistics["confidence_trends"] == {}
    assert "last_updated" in history.statistics
