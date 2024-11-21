import pytest
from pydantic import ValidationError
from models.curation_models import CategoryHierarchy, CurationDetails, EnhancedCurationDetails

def test_category_hierarchy_valid():
    category = CategoryHierarchy(
        main_category="AI/ML",
        subcategory="Deep Learning",
        confidence=0.95,
        reasoning="Repository contains deep learning frameworks"
    )
    assert category.main_category == "AI/ML"
    assert category.subcategory == "Deep Learning"
    assert category.confidence == 0.95
    assert category.reasoning == "Repository contains deep learning frameworks"

def test_category_hierarchy_invalid_confidence():
    with pytest.raises(ValidationError):
        CategoryHierarchy(
            main_category="AI/ML",
            subcategory="Deep Learning",
            confidence=1.5,  # Invalid: > 1.0
            reasoning="Test"
        )

def test_category_hierarchy_missing_reasoning():
    with pytest.raises(ValidationError):
        CategoryHierarchy(
            main_category="AI/ML",
            subcategory="Deep Learning",
            confidence=0.95,
            reasoning=""  # Invalid: empty string
        )

def test_category_hierarchy_optional_subcategory():
    category = CategoryHierarchy(
        main_category="AI/ML",
        confidence=0.95,
        reasoning="General AI/ML repository"
    )
    assert category.main_category == "AI/ML"
    assert category.subcategory is None
    assert category.confidence == 0.95

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
                subcategory="Deep Learning",
                confidence=0.95,
                reasoning="Contains deep learning frameworks"
            )
        ],
        related_repos=["repo1", "repo2"],
        consensus_data={
            "agent_decisions": {
                "category_agent": "AI/ML",
                "review_agent": "AI/ML"
            }
        },
        version="1.0.0"
    )
    assert len(details.categories) == 1
    assert details.categories[0].main_category == "AI/ML"
    assert len(details.related_repos) == 2
    assert details.version == "1.0.0"

def test_enhanced_curation_details_invalid_version():
    with pytest.raises(ValidationError):
        EnhancedCurationDetails(
            tags=["python"],
            popularity_score=0.85,
            trending_score=0.75,
            categories=[
                CategoryHierarchy(
                    main_category="AI/ML",
                    confidence=0.95,
                    reasoning="Test"
                )
            ],
            version="invalid"  # Invalid version format
        )

def test_enhanced_curation_details_empty_categories():
    with pytest.raises(ValidationError):
        EnhancedCurationDetails(
            tags=["python"],
            popularity_score=0.85,
            trending_score=0.75,
            categories=[],  # Invalid: empty categories list
            version="1.0.0"
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
                reasoning="Test"
            )
        ]
    )
    assert details.related_repos == []
    assert details.consensus_data == {}
    assert details.version == "1.0.0"  # Default version
