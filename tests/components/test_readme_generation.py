"""Component test for README generation using live database content."""

import logging
from pathlib import Path

import pytest
from agents.readme_generator import ReadmeGenerator
from db.connection import Database
from tests.components.conftest import print_repository_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ReadmeGeneration - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('component_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
class TestReadmeGenerationComponent:
    """Test README generation with live database content."""

    @pytest.fixture(scope="class")
    def db(self):
        """Get database connection with content from previous component tests."""
        db = Database("tests/test.db")  # Use the test database where content extractor stored data
        db.connect()
        yield db
        db.disconnect()

    @pytest.fixture(scope="class")
    def readme_generator(self, db):
        """Create ReadmeGenerator instance."""
        return ReadmeGenerator(db)

    async def write_test_readme(self, content: str) -> tuple[bool, str]:
        """Write content to test README file with incremental naming.
        
        Args:
            content: Markdown content to write
            
        Returns:
            Tuple of (success: bool, filename: str)
        """
        try:
            base_path = Path("readme.test.md")
            file_path = base_path
            counter = 1
            
            # Find first available filename
            while file_path.exists():
                file_path = Path(f"readme.test.{counter}.md")
                counter += 1
            
            file_path.write_text(content)
            return True, file_path.name
        except Exception as e:
            logger.error(f"Failed to write test README: {e}")
            return False, ""

    async def test_readme_generation(self, readme_generator, db):
        """Test README generation with live database content."""
        logger.info("Starting README generation test")
        print("\n=== README Generation Component Test ===")

        try:
            # Get current repository and topic counts for logging
            repositories = await db.get_repositories()
            topics = await db.get_topics()
            
            repo_count = len(repositories)
            topic_count = len(topics)
            
            print(f"\nInitial Data:")
            print(f"Found {repo_count} repositories and {topic_count} topics in database")

            # Print sample of repositories
            print("\nSample Repositories:")
            print_repository_summary("Sample Repositories", repositories[:3])  # Show first 3

            # Generate markdown
            print("\nGenerating README content...")
            markdown = await readme_generator.generate_markdown()
            
            # Write to test file
            success, filename = await self.write_test_readme(markdown)
            assert success, "Failed to write test README file"
            print(f"✓ README file written successfully to {filename}")

            # Log file stats
            test_file = Path(filename)
            content = test_file.read_text()
            file_size = test_file.stat().st_size
            line_count = len(content.split("\n"))
            print(f"\nGenerated README Statistics:")
            print(f"- File size: {file_size} bytes")
            print(f"- Line count: {line_count}")

            logger.info("README generation test completed successfully")
            print("\nREADME generation test completed successfully")
            
        except Exception as e:
            logger.error(f"README generation test failed: {str(e)}")
            raise
