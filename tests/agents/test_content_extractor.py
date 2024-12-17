"""Tests for content extraction and repository summarization agent."""

import pytest
from datetime import datetime, UTC
from unittest.mock import patch, AsyncMock
import json
import os
import yaml

from pydantic_ai import Agent
from agents.content_extractor import ContentExtractorAgent, ContentExtractionError, CategoryValidationError
from db.connection import Database
from db.migrations import MigrationManager
from tests.config import get_test_settings

def print_categories(summary: Dict[str, Any], prefix: str = "") -> None:
    """Print category information in a human-readable format."""
    print(f"\n{prefix}Repository Analysis:")
    print(f"{'='*50}")
    print(f"Is GenAI: {summary.get('is_genai', False)}")
    
    if not summary.get('is_genai', False):
        print(f"Other Category: {summary.get('other_category_description', 'N/A')}")
        return
    
    print("\nRanked Categories:")
    for cat in summary.get('ranked_categories', []):
        print(f"{cat['rank']}. {cat['category']}")
    
    if 'new_category_suggestion' in summary:
        suggestion = summary['new_category_suggestion']
        print("\nNew Category Suggestion:")
        print(f"Name: {suggestion['name']}")
        print(f"Parent: {suggestion.get('parent_category', 'N/A')}")
        print(f"Description: {suggestion['description']}")
        print(f"Differentiation: {suggestion['differentiation']}")

@pytest.fixture
def test_db():
    """Set up test database with migrations."""
    settings = get_test_settings()
    
    # Remove existing test database if it exists
    if os.path.exists(settings.TEST_DATABASE_PATH):
        os.remove(settings.TEST_DATABASE_PATH)
    
    # Create new database and apply migrations
    db = Database(str(settings.TEST_DATABASE_PATH))
    migration_manager = MigrationManager(db)
    migration_manager.apply_migrations()
    
    yield db
    
    # Clean up
    db.disconnect()
    if os.path.exists(settings.TEST_DATABASE_PATH):
        os.remove(settings.TEST_DATABASE_PATH)

@pytest.fixture
def mock_github_response():
    return {
        'name': 'test-repo',
        'full_name': 'user/test-repo',
        'description': 'A test repository',
        'stargazers_count': 100,
        'forks_count': 50,
        'language': 'Python',
        'topics': ['ai', 'machine-learning'],
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-02T00:00:00Z'
    }

@pytest.fixture
def mock_readme_response():
    return {
        'content': 'IyBUZXN0IFJlcG9zaXRvcnkKCkEgdGVzdCByZXBvc2l0b3J5IGZvciBBSS9NTC4='  # Base64 encoded
    }

@pytest.fixture
def mock_genai_summary_response():
    return {
        'is_genai': True,
        'primary_purpose': 'Test AI/ML functionality',
        'key_technologies': ['python', 'pytorch', 'transformers'],
        'target_users': 'ML researchers and developers',
        'main_features': ['model training', 'inference', 'evaluation'],
        'technical_domain': 'Machine Learning',
        'ranked_categories': [
            {'rank': 1, 'category': 'Model Development/Model architectures'},
            {'rank': 2, 'category': 'MLOps and LLMOps/Experiment tracking'},
            {'rank': 3, 'category': 'Evaluation and Testing/Model analysis and debugging'}
        ]
    }

@pytest.fixture
def mock_invalid_category_summary_response():
    return {
        'is_genai': True,
        'primary_purpose': 'Test AI/ML functionality',
        'key_technologies': ['python', 'pytorch', 'transformers'],
        'target_users': 'ML researchers and developers',
        'main_features': ['model training', 'inference', 'evaluation'],
        'technical_domain': 'Machine Learning',
        'ranked_categories': [
            {'rank': 1, 'category': 'Invalid Category'},  # Invalid
            {'rank': 2, 'category': 'Model Development'},  # Valid top-level
            {'rank': 3, 'category': 'Model architectures'}  # Missing parent
        ]
    }

@pytest.fixture
def mock_corrected_category_summary_response():
    return {
        'is_genai': True,
        'primary_purpose': 'Test AI/ML functionality',
        'key_technologies': ['python', 'pytorch', 'transformers'],
        'target_users': 'ML researchers and developers',
        'main_features': ['model training', 'inference', 'evaluation'],
        'technical_domain': 'Machine Learning',
        'ranked_categories': [
            {'rank': 1, 'category': 'Model Development/Model architectures'},
            {'rank': 2, 'category': 'Model Development'},
            {'rank': 3, 'category': 'Evaluation and Testing/Benchmarking'}
        ]
    }

@pytest.fixture
def mock_non_genai_summary_response():
    return {
        'is_genai': False,
        'other_category_description': 'Web development framework',
        'primary_purpose': 'Web application development',
        'key_technologies': ['javascript', 'react', 'node'],
        'target_users': 'Web developers',
        'main_features': ['routing', 'state management'],
        'technical_domain': 'Web Development'
    }

@pytest.fixture
def mock_new_category_summary_response():
    return {
        'is_genai': True,
        'primary_purpose': 'Novel LLM training approach',
        'key_technologies': ['python', 'pytorch', 'custom-training'],
        'target_users': 'ML researchers',
        'main_features': ['efficient training', 'novel architecture'],
        'technical_domain': 'Machine Learning',
        'ranked_categories': [
            {'rank': 1, 'category': 'Model Development/Model architectures'},
            {'rank': 2, 'category': 'Optimization/Performance optimization'}
        ],
        'new_category_suggestion': {
            'name': 'Training Innovations',
            'parent_category': 'Model Development',
            'description': 'Novel approaches to LLM training that differ significantly from standard methods',
            'example_repos': ['user/repo1', 'user/repo2'],
            'differentiation': 'Focuses on innovative training methods not covered by existing categories'
        }
    }

@pytest.fixture
def content_extractor(test_db):
    """Create content extractor with test database and max_age_hours=0."""
    settings = get_test_settings()
    return ContentExtractorAgent(
        github_token=settings.GITHUB_TOKEN,
        db=test_db,
        max_age_hours=0  # Always update for testing
    )

@pytest.fixture
def sample_newsletter_content():
    return """
    Check out these awesome projects:
    
    1. https://github.com/user1/repo1 - A cool LLM project
    2. https://github.com/user2/repo2/ - Vector database implementation
    Not a repo: https://example.com
    Another repo: https://github.com/user3/repo3#readme - Web framework
    """

def test_taxonomy_loading(content_extractor):
    """Test that taxonomy is properly loaded."""
    assert content_extractor.taxonomy is not None
    assert "Model Development" in content_extractor.taxonomy
    assert "subcategories" in content_extractor.taxonomy["Model Development"]
    assert "Model architectures" in content_extractor.taxonomy["Model Development"]["subcategories"]

def test_validate_categories(content_extractor, mock_genai_summary_response, mock_invalid_category_summary_response):
    """Test category validation against taxonomy."""
    print("\nTesting Category Validation")
    print("="*50)
    
    # Test valid categories
    print("\nValidating correct categories:")
    print_categories(mock_genai_summary_response)
    invalid_cats = content_extractor.validate_categories(mock_genai_summary_response)
    assert len(invalid_cats) == 0
    
    # Test invalid categories
    print("\nValidating incorrect categories:")
    print_categories(mock_invalid_category_summary_response)
    invalid_cats = content_extractor.validate_categories(mock_invalid_category_summary_response)
    print(f"\nInvalid categories found: {invalid_cats}")
    assert len(invalid_cats) == 2
    assert "Invalid Category" in invalid_cats
    assert "Model architectures" in invalid_cats  # Missing parent category

@pytest.mark.asyncio
async def test_category_validation_retry(
    content_extractor,
    mock_github_response,
    mock_readme_response,
    mock_invalid_category_summary_response,
    mock_corrected_category_summary_response
):
    """Test LLM retry with category validation feedback."""
    print("\nTesting Category Validation Retry")
    print("="*50)
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.side_effect = [
            AsyncMock(status=200, json=AsyncMock(return_value=mock_github_response))(),
            AsyncMock(status=200, json=AsyncMock(return_value=mock_readme_response))()
        ]
        
        # Mock LLM responses - first invalid, then corrected
        with patch.object(
            content_extractor.summarization_agent,
            'complete'
        ) as mock_complete:
            mock_complete.side_effect = [
                AsyncMock(content=json.dumps(mock_invalid_category_summary_response))(),
                AsyncMock(content=json.dumps(mock_corrected_category_summary_response))()
            ]
            
            print("\nFirst attempt (with invalid categories):")
            print_categories(mock_invalid_category_summary_response)
            
            print("\nSecond attempt (with corrected categories):")
            print_categories(mock_corrected_category_summary_response)
            
            result = await content_extractor.process_newsletter_content(
                email_id="test123",
                content="https://github.com/user1/repo1 - LLM project"
            )
    
    assert len(result) == 1
    repo = result[0]
    assert repo["repository_id"] > 0
    
    print("\nFinal stored categories:")
    print_categories(repo["summary"])
    
    # Verify corrected categories were used
    categories = repo["summary"]["ranked_categories"]
    assert all(
        content_extractor.validate_categories({"is_genai": True, "ranked_categories": [cat]}) == []
        for cat in categories
    )

@pytest.mark.asyncio
async def test_process_genai_repository(
    content_extractor,
    mock_github_response,
    mock_readme_response,
    mock_genai_summary_response
):
    """Test processing a GenAI repository."""
    print("\nTesting GenAI Repository Processing")
    print("="*50)
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.side_effect = [
            AsyncMock(status=200, json=AsyncMock(return_value=mock_github_response))(),
            AsyncMock(status=200, json=AsyncMock(return_value=mock_readme_response))()
        ]
        
        with patch.object(
            content_extractor.summarization_agent,
            'complete',
            return_value=AsyncMock(content=json.dumps(mock_genai_summary_response))
        ):
            result = await content_extractor.process_newsletter_content(
                email_id="test123",
                content="https://github.com/user1/repo1 - LLM project"
            )
    
    assert len(result) == 1
    repo = result[0]
    print_categories(repo["summary"])
    
    assert repo["repository_id"] > 0
    assert repo["summary"]["is_genai"] is True
    assert len(repo["summary"]["ranked_categories"]) == 3
    
    # Verify categories were stored
    print("\nStored Categories in Database:")
    for category in repo["summary"]["ranked_categories"]:
        topic = content_extractor.db.fetch_one(
            "SELECT * FROM topics WHERE name = ?",
            (category["category"],)
        )
        assert topic is not None
        print(f"- {category['category']} (confidence: {1.0/category['rank']:.2f})")
        
        category_rel = content_extractor.db.fetch_one(
            """
            SELECT * FROM repository_categories 
            WHERE repository_id = ? AND topic_id = ?
            """,
            (repo["repository_id"], topic["id"])
        )
        assert category_rel is not None
        assert category_rel["confidence_score"] == pytest.approx(1.0 / category["rank"])

@pytest.mark.asyncio
async def test_process_non_genai_repository(
    content_extractor,
    mock_github_response,
    mock_readme_response,
    mock_non_genai_summary_response
):
    """Test processing a non-GenAI repository."""
    print("\nTesting Non-GenAI Repository Processing")
    print("="*50)
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.side_effect = [
            AsyncMock(status=200, json=AsyncMock(return_value=mock_github_response))(),
            AsyncMock(status=200, json=AsyncMock(return_value=mock_readme_response))()
        ]
        
        with patch.object(
            content_extractor.summarization_agent,
            'complete',
            return_value=AsyncMock(content=json.dumps(mock_non_genai_summary_response))
        ):
            result = await content_extractor.process_newsletter_content(
                email_id="test123",
                content="https://github.com/user1/repo1 - Web framework"
            )
    
    assert len(result) == 1
    repo = result[0]
    print_categories(repo["summary"])
    
    assert repo["repository_id"] == 0  # Should not be stored in database
    assert repo["summary"]["is_genai"] is False
    assert "other_category_description" in repo["summary"]
    assert "ranked_categories" not in repo["summary"]
    
    # Verify nothing was stored in database
    count = content_extractor.db.fetch_one(
        "SELECT COUNT(*) as count FROM repositories"
    )["count"]
    assert count == 0

@pytest.mark.asyncio
async def test_process_new_category_repository(
    content_extractor,
    mock_github_response,
    mock_readme_response,
    mock_new_category_summary_response
):
    """Test processing a repository that suggests a new category."""
    print("\nTesting New Category Suggestion")
    print("="*50)
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.side_effect = [
            AsyncMock(status=200, json=AsyncMock(return_value=mock_github_response))(),
            AsyncMock(status=200, json=AsyncMock(return_value=mock_readme_response))()
        ]
        
        with patch.object(
            content_extractor.summarization_agent,
            'complete',
            return_value=AsyncMock(content=json.dumps(mock_new_category_summary_response))
        ):
            result = await content_extractor.process_newsletter_content(
                email_id="test123",
                content="https://github.com/user1/repo1 - Novel LLM training"
            )
    
    assert len(result) == 1
    repo = result[0]
    print_categories(repo["summary"])
    
    assert repo["repository_id"] > 0  # Should be stored in database
    assert repo["summary"]["is_genai"] is True
    assert "new_category_suggestion" in repo["summary"]
    suggestion = repo["summary"]["new_category_suggestion"]
    assert suggestion["name"] == "Training Innovations"
    assert suggestion["parent_category"] == "Model Development"
    
    # Verify it was still categorized with existing categories
    print("\nStored Categories in Database:")
    stored_categories = content_extractor.db.fetch_all(
        """
        SELECT t.name, rc.confidence_score
        FROM repository_categories rc
        JOIN topics t ON rc.topic_id = t.id
        WHERE rc.repository_id = ?
        ORDER BY rc.confidence_score DESC
        """,
        (repo["repository_id"],)
    )
    for cat in stored_categories:
        print(f"- {cat['name']} (confidence: {cat['confidence_score']:.2f})")
    assert len(stored_categories) == 2

@pytest.mark.asyncio
async def test_should_update_repository(content_extractor):
    """Test repository update check logic."""
    repo_url = "https://github.com/user/test-repo"
    
    # Should update when repository doesn't exist
    assert await content_extractor._should_update_repository(repo_url) is True
    
    # Add repository
    now = datetime.now(UTC)
    content_extractor.db.execute(
        """
        INSERT INTO repositories (
            github_url, first_seen_date, last_mentioned_date,
            mention_count, metadata
        ) VALUES (?, ?, ?, 1, ?)
        """,
        (
            repo_url,
            now.isoformat(),
            now.isoformat(),
            json.dumps({"test": "data"})
        )
    )
    
    # Should still update since max_age_hours is 0
    assert await content_extractor._should_update_repository(repo_url) is True
    
    # Create extractor with non-zero max_age_hours
    new_extractor = ContentExtractorAgent(
        github_token="test_token",
        db=content_extractor.db,
        max_age_hours=24
    )
    
    # Should not update since repository was just added
    assert await new_extractor._should_update_repository(repo_url) is False

def test_validate_github_url(content_extractor):
    """Test GitHub URL validation."""
    valid_urls = [
        "https://github.com/user/repo",
        "https://github.com/user/repo/",
        "https://github.com/user/repo#readme"
    ]
    invalid_urls = [
        "https://example.com",
        "http://github.com/user",
        "https://github.com",
        None
    ]
    
    for url in valid_urls:
        assert content_extractor.validate_github_url(url) is True
    
    for url in invalid_urls:
        assert content_extractor.validate_github_url(url) is False
