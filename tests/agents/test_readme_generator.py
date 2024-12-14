"""Tests for the README Generator agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel

pytestmark = pytest.mark.asyncio

# Mock data structures
class Repository(BaseModel):
    """Repository data model."""
    github_url: str
    description: str
    topics: list[dict]
    stars: int = 0
    last_updated: str = ""

@pytest.fixture
def mock_db():
    """Create mock database connection."""
    db = AsyncMock()
    db.get_repositories = AsyncMock(return_value=[
        Repository(
            github_url="https://github.com/org/ml-project",
            description="A machine learning framework",
            topics=[{"topic_id": 1, "confidence_score": 0.9}],
            stars=1000,
            last_updated="2024-01-15"
        ),
        Repository(
            github_url="https://github.com/org/nlp-tool",
            description="Natural language processing tool",
            topics=[{"topic_id": 2, "confidence_score": 0.85}],
            stars=500,
            last_updated="2024-01-14"
        )
    ])
    db.get_topics = AsyncMock(return_value={
        1: {"name": "Machine Learning", "parent_id": None},
        2: {"name": "Natural Language Processing", "parent_id": 1}
    })
    return db

@pytest.fixture
def mock_github_client():
    """Create mock GitHub client."""
    client = AsyncMock()
    client.update_readme = AsyncMock(return_value=True)
    return client

@pytest.fixture
def mock_openai():
    """Create mock OpenAI client."""
    with patch('openai.AsyncOpenAI') as mock:
        mock.return_value.chat.completions.create = AsyncMock(return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="Test response"))]
        ))
        yield mock

@pytest.fixture
def readme_generator(mock_db, mock_github_client, mock_openai):
    """Create ReadmeGenerator instance with mocks."""
    from agents.readme_generator import ReadmeGenerator
    with patch('pydantic_ai.models.openai.cached_async_http_client'):
        return ReadmeGenerator(mock_db, mock_github_client)

class TestReadmeGenerator:
    """Test suite for ReadmeGenerator."""

    async def test_generate_markdown(self, readme_generator):
        """Test markdown generation with categories."""
        markdown = await readme_generator.generate_markdown()
        
        assert isinstance(markdown, str)
        assert "# AI/ML GitHub Repository List" in markdown
        assert "## Machine Learning" in markdown
        assert "## Natural Language Processing" in markdown
        assert "https://github.com/org/ml-project" in markdown
        assert "https://github.com/org/nlp-tool" in markdown

    async def test_category_organization(self, readme_generator):
        """Test repositories are organized by correct categories."""
        markdown = await readme_generator.generate_markdown()
        
        # ML project should appear before NLP tool (parent before child)
        ml_pos = markdown.find("https://github.com/org/ml-project")
        nlp_pos = markdown.find("https://github.com/org/nlp-tool")
        assert ml_pos < nlp_pos
        
        # Each repo should be under its category
        ml_header_pos = markdown.find("## Machine Learning")
        nlp_header_pos = markdown.find("## Natural Language Processing")
        assert ml_header_pos < ml_pos < nlp_header_pos < nlp_pos

    async def test_repository_formatting(self, readme_generator):
        """Test individual repository entry formatting."""
        markdown = await readme_generator.generate_markdown()
        
        # Check repository formatting
        assert "- [ml-project](https://github.com/org/ml-project)" in markdown
        assert "A machine learning framework" in markdown
        assert "⭐ 1000" in markdown
        assert "Updated: 2024-01-15" in markdown

    async def test_empty_category_handling(self, readme_generator, mock_db):
        """Test handling of categories with no repositories."""
        # Mock empty repository list
        mock_db.get_repositories.return_value = []
        
        markdown = await readme_generator.generate_markdown()
        
        assert isinstance(markdown, str)
        assert "No repositories found" in markdown

    async def test_github_integration(self, readme_generator, mock_github_client):
        """Test GitHub README update integration."""
        await readme_generator.update_github_readme()
        
        mock_github_client.update_readme.assert_called_once()
        # Verify markdown was passed to update method
        call_args = mock_github_client.update_readme.call_args[0]
        assert isinstance(call_args[0], str)
        assert "# AI/ML GitHub Repository List" in call_args[0]

    async def test_invalid_repository_handling(self, readme_generator, mock_db):
        """Test handling of invalid repository data."""
        # Mock invalid repository data
        mock_db.get_repositories.return_value = [
            Repository(
                github_url="",  # Invalid URL
                description="Test",
                topics=[{"topic_id": 1, "confidence_score": 0.9}]
            )
        ]
        
        with pytest.raises(ValueError, match="Invalid repository URL"):
            await readme_generator.generate_markdown()

    async def test_markdown_structure_validation(self, readme_generator):
        """Test generated markdown structure validity."""
        markdown = await readme_generator.generate_markdown()
        
        # Verify basic markdown structure
        lines = markdown.split('\n')
        
        # Title should be h1
        assert lines[0].startswith('# ')
        assert not lines[0].startswith('## ')
        
        # Categories should be h2
        category_lines = [line for line in lines if line.startswith('##')]
        assert len(category_lines) > 0
        for line in category_lines:
            assert line.startswith('## ')
            assert not line.startswith('### ')
        
        # Repository entries should be list items
        repo_lines = [line for line in lines if line.startswith('- ')]
        assert len(repo_lines) > 0
        for line in repo_lines:
            # Verify repository line format
            assert '](' in line  # Link format
            assert '⭐' in line  # Stars
            assert 'Updated:' in line  # Update date
