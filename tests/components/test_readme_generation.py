"""Component test for README generation using live database content."""

import logging
import pytest
from pathlib import Path
from datetime import datetime

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

    async def write_test_readme(self, content: str) -> bool:
        """Write content to test README file.
        
        Args:
            content: Markdown content to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            test_file = Path("readme.test.md")
            test_file.write_text(content)
            return True
        except Exception as e:
            logger.error(f"Failed to write test README: {e}")
            return False

    async def test_live_data_generation(self, readme_generator, db):
        """Test README generation with live database content."""
        logger.info("Starting live data README generation test")
        print("\n=== README Generation Component Test ===")
        print("\nStarting live data generation test...")

        try:
            # Get current repository and topic counts
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
            
            # Basic validation
            assert "# AI/ML GitHub Repository List" in markdown
            print("\nValidation:")
            print("✓ Title present")
            
            # Verify all repositories are included
            missing_repos = []
            for repo in repositories:
                repo_url = repo['github_url']
                if repo_url not in markdown:
                    missing_repos.append(repo_url)
            
            assert not missing_repos, f"Missing repositories: {missing_repos}"
            print(f"✓ All {repo_count} repositories included")

            # Verify all topics are represented
            missing_topics = []
            for topic_id, topic in topics.items():
                topic_name = topic['name']
                if not topic.get('parent_id'):  # Use get() to handle missing parent_id
                    if f"## {topic_name}" not in markdown:
                        missing_topics.append(topic_name)
                else:
                    if f"### {topic_name}" not in markdown:
                        missing_topics.append(topic_name)
            
            assert not missing_topics, f"Missing topics: {missing_topics}"
            print(f"✓ All {topic_count} topics included")

            # Log sample of generated content
            print("\nPreview of generated content:")
            print("=" * 80)
            content_preview = "\n".join(markdown.split("\n")[:10])
            print(content_preview)
            print("=" * 80)

            logger.info("Live data README generation test completed successfully")
            print("\nLive data generation test completed successfully")
            
        except Exception as e:
            logger.error(f"Live data README generation test failed: {str(e)}")
            raise

    async def test_category_organization(self, readme_generator):
        """Test proper organization of repositories by category."""
        logger.info("Starting category organization test")
        print("\nStarting category organization test...")

        try:
            # Get category structure
            structure = await readme_generator.db.get_topics()
            
            # Generate markdown
            markdown = await readme_generator.generate_markdown()
            
            print("\nVerifying category hierarchy:")
            # Verify parent categories come before child categories
            for topic_id, topic in structure.items():
                if not topic.get('parent_id'):  # Use get() to handle missing parent_id
                    parent_pos = markdown.find(f"## {topic['name']}")
                    assert parent_pos >= 0, f"Parent category not found: {topic['name']}"
                    print(f"✓ Found parent category: {topic['name']}")
                    
                    # Find child topics
                    children = [t for t in structure.values() if t.get('parent_id') == topic_id]
                    for child in children:
                        child_pos = markdown.find(f"### {child['name']}")
                        assert child_pos >= 0, f"Child category not found: {child['name']}"
                        assert parent_pos < child_pos, f"Child topic {child['name']} appears before parent {topic['name']}"
                        print(f"  ✓ Found child category: {child['name']} (after parent)")

            logger.info("Category organization test completed successfully")
            print("\nCategory organization test completed successfully")
            
        except Exception as e:
            logger.error(f"Category organization test failed: {str(e)}")
            raise

    async def test_repository_metadata(self, readme_generator):
        """Test inclusion of repository metadata (stars, updates, etc)."""
        logger.info("Starting repository metadata test")
        print("\nStarting repository metadata test...")

        try:
            markdown = await readme_generator.generate_markdown()
            repositories = await readme_generator.db.get_repositories()

            print("\nVerifying repository metadata:")
            for repo in repositories:
                # Verify each repository's metadata is included
                repo_url = repo['github_url']
                repo_name = repo_url.split('/')[-1]
                
                # Find repository entry in markdown
                repo_line = next(
                    line for line in markdown.split('\n') 
                    if repo_url in line
                )
                
                # Get metadata from JSON if needed
                metadata = repo.get('metadata', {})
                if isinstance(metadata, str):
                    import json
                    metadata = json.loads(metadata)
                
                # Verify metadata
                assert f"[{repo_name}]" in repo_line, f"Repository name not formatted correctly: {repo_name}"
                assert str(metadata.get('stars', 0)) in repo_line, f"Stars count missing for {repo_name}"
                assert metadata.get('updated_at', '') in repo_line, f"Update date missing for {repo_name}"
                
                print(f"✓ Verified metadata for {repo_name}")
                print(f"  Entry: {repo_line.strip()}")

            logger.info("Repository metadata test completed successfully")
            print("\nRepository metadata test completed successfully")
            
        except Exception as e:
            logger.error(f"Repository metadata test failed: {str(e)}")
            raise

    async def test_readme_file_generation(self, readme_generator):
        """Test generation of actual README file."""
        logger.info("Starting README file generation test")
        print("\nStarting README file generation test...")

        try:
            # Generate markdown
            markdown = await readme_generator.generate_markdown()
            
            # Write to test file
            success = await self.write_test_readme(markdown)
            assert success, "Failed to write test README file"
            print("✓ README file written successfully")

            # Verify test file was created
            test_file = Path("readme.test.md")
            assert test_file.exists(), "Test README file was not created"
            print("✓ Test file exists")
            
            # Read and validate content
            content = test_file.read_text()
            assert content.startswith("# AI/ML GitHub Repository List")
            print("✓ Content validation passed")
            
            # Log file stats
            file_size = test_file.stat().st_size
            line_count = len(content.split("\n"))
            print(f"\nGenerated README Statistics:")
            print(f"- File size: {file_size} bytes")
            print(f"- Line count: {line_count}")

            logger.info("README file generation test completed successfully")
            print("\nREADME file generation test completed successfully")
            
        except Exception as e:
            logger.error(f"README file generation test failed: {str(e)}")
            raise

    async def test_end_to_end_flow(self, readme_generator):
        """Test complete README generation flow with verification output."""
        logger.info("Starting end-to-end README generation test")
        print("\n=== End-to-End README Generation Test ===")

        try:
            # 1. Get initial data
            repositories = await readme_generator.db.get_repositories()
            topics = await readme_generator.db.get_topics()
            
            initial_stats = {
                "repository_count": len(repositories),
                "topic_count": len(topics),
                "parent_topics": len([t for t in topics.values() if not t.get('parent_id')]),
                "child_topics": len([t for t in topics.values() if t.get('parent_id')])
            }
            
            print("\nInitial Statistics:")
            for key, value in initial_stats.items():
                print(f"  {key}: {value}")

            # 2. Generate README
            print("\nGenerating README...")
            markdown = await readme_generator.generate_markdown()
            success = await self.write_test_readme(markdown)
            assert success, "Failed to write test README file"
            print("✓ README generation successful")

            # 3. Analyze generated content
            test_file = Path("readme.test.md")
            content = test_file.read_text()
            
            generation_stats = {
                "total_size": len(content),
                "line_count": len(content.split("\n")),
                "category_count": content.count("##"),
                "repository_entries": content.count("- ["),
                "timestamp": datetime.now().isoformat()
            }
            
            print("\nGeneration Statistics:")
            for key, value in generation_stats.items():
                print(f"  {key}: {value}")

            # 4. Verify content structure
            structure_validation = {
                "has_title": content.startswith("# AI/ML GitHub Repository List"),
                "has_categories": "##" in content,
                "has_repositories": "- [" in content,
                "has_metadata": "⭐" in content and "Updated:" in content
            }
            
            print("\nContent Validation:")
            for key, value in structure_validation.items():
                print(f"  {key}: {'✓' if value else '✗'}")
                assert value, f"Failed validation: {key}"

            logger.info("End-to-end README generation test completed successfully")
            print("\nEnd-to-end README generation test completed successfully")
            
        except Exception as e:
            logger.error(f"End-to-end README generation test failed: {str(e)}")
            raise
