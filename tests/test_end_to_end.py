"""End-to-end tests for the complete GitHub repository curation workflow."""

import os
import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from processing.embedchain_store import EmbedchainStore
from processing.gmail.client import GmailClient
from agents.orchestrator import AgentOrchestrator
from agents.newsletter_monitor import NewsletterMonitor
from agents.content_extractor import ContentExtractorAgent
from agents.topic_analyzer import TopicAnalyzer
from agents.repository_curator import RepositoryCurator
from agents.readme_generator import ReadmeGenerator

pytestmark = pytest.mark.asyncio

class TestEndToEndWorkflow:
    """End-to-end test suite for the complete workflow."""

    @pytest.fixture
    def mock_github_client(self):
        """Create mock GitHub client with repository data."""
        client = AsyncMock()
        client.get_repository_info.return_value = {
            'name': 'ml-project',
            'full_name': 'test/ml-project',
            'description': 'A new machine learning framework',
            'stars': 1000,
            'forks': 500,
            'language': 'Python',
            'topics': ['machine-learning', 'ai', 'deep-learning'],
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-15T00:00:00Z',
            'readme_content': '# ML Project\n\nFast and easy machine learning framework.'
        }
        client.update_readme.return_value = True
        return client

    @pytest.fixture
    def mock_db(self):
        """Create mock database with test data."""
        db = AsyncMock()
        db.get_repositories.return_value = [
            {
                'github_url': 'https://github.com/test/ml-project',
                'name': 'ml-project',
                'description': 'A new machine learning framework',
                'summary': {
                    'primary_purpose': 'Provide an easy-to-use ML framework',
                    'key_technologies': ['python', 'pytorch', 'tensorflow'],
                    'target_users': 'ML researchers and developers',
                    'main_features': ['model training', 'inference', 'evaluation'],
                    'technical_domain': 'Machine Learning'
                },
                'metadata': {
                    'stars': 1000,
                    'forks': 500,
                    'language': 'Python',
                    'topics': ['machine-learning', 'ai', 'deep-learning'],
                    'created_at': '2024-01-01T00:00:00Z',
                    'updated_at': '2024-01-15T00:00:00Z'
                },
                'topics': [{'topic_id': 1, 'score': 0.9}],
                'first_seen_date': '2024-01-15T00:00:00Z',
                'source_type': 'newsletter',
                'source_id': 'email123'
            }
        ]
        db.get_topics.return_value = {
            1: {'name': 'Machine Learning', 'parent_id': None},
            2: {'name': 'Deep Learning', 'parent_id': 1}
        }
        return db

    def _get_credentials(self, credentials_path: str, token_path: str, scopes: list) -> Credentials:
        """Get or refresh Google API credentials."""
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, scopes)
                # Set redirect URI with trailing slash to match credentials config
                flow.redirect_uri = "http://localhost:8029/"
                # Use port 8029 to match the configured redirect URI
                creds = flow.run_local_server(
                    port=8029,
                    access_type='offline',  # Enable offline access
                    prompt='consent'  # Force consent screen to get refresh token
                )

            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        return creds

    @pytest.fixture
    async def test_system(self, mock_github_client, mock_db, tmp_path):
        """Create complete test system with real components."""
        # Set up vector storage with real credentials
        vector_db_path = tmp_path / "vector_store"
        os.makedirs(vector_db_path, exist_ok=True)
        
        # Set up credentials paths
        credentials_path = ".credentials/google-credentials.json"
        token_path = os.path.join(vector_db_path, "token.json")
        
        # Get authorized credentials
        creds = self._get_credentials(
            credentials_path=credentials_path,
            token_path=token_path,
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        
        # Create EmbedchainStore with authorized token
        embedchain_store = EmbedchainStore(token_path)
        
        # Create real Gmail client
        gmail_client = GmailClient(credentials_path, token_path)
        
        # Create agents with real implementations
        newsletter_monitor = NewsletterMonitor(gmail_client, embedchain_store)
        content_extractor = ContentExtractorAgent(
            embedchain_store,
            github_token=os.getenv('GITHUB_TOKEN', 'test-token')
        )
        topic_analyzer = TopicAnalyzer(embedchain_store)
        repository_curator = RepositoryCurator(embedchain_store)
        readme_generator = ReadmeGenerator(mock_db, mock_github_client)
        
        # Create orchestrator
        orchestrator = AgentOrchestrator(
            embedchain_store=embedchain_store,
            newsletter_monitor=newsletter_monitor,
            content_extractor=content_extractor,
            topic_analyzer=topic_analyzer,
            repository_curator=repository_curator,
            readme_generator=readme_generator
        )
        
        return {
            'orchestrator': orchestrator,
            'store': embedchain_store,
            'gmail_client': gmail_client,
            'github_client': mock_github_client,
            'vector_db_path': vector_db_path
        }

    async def test_real_readme_generation(self, test_system):
        """Test actual generation of readme.test.md using real components."""
        from pydantic import BaseModel, ConfigDict
        from pydantic_ai import Agent, RunContext
        
        class ReadmeTestDeps(BaseModel):
            """Dependencies for readme test generation."""
            orchestrator: AgentOrchestrator
            output_path: str = "readme.test.md"
            
            model_config = ConfigDict(arbitrary_types_allowed=True)

        # Create agent for readme generation
        agent = Agent(
            "openai:gpt-4",
            deps_type=ReadmeTestDeps,
            result_type=bool,
            system_prompt=(
                "Generate a real README.md file by running the complete pipeline "
                "and saving the output to the specified path. The README should "
                "showcase real AI/ML GitHub repositories with proper categorization "
                "and include repository summaries."
            )
        )

        @agent.tool
        async def run_pipeline_and_save(ctx: RunContext[ReadmeTestDeps]) -> str:
            """Run the complete pipeline and save output to readme.test.md."""
            # Run the pipeline
            result = await ctx.deps.orchestrator.run_pipeline()
            if not result:
                raise ValueError("Pipeline execution failed")

            # Get the generated markdown content
            readme_content = await ctx.deps.orchestrator.readme_generator.generate_markdown()

            # Save to readme.test.md
            with open(ctx.deps.output_path, 'w') as f:
                f.write(readme_content)

            return f"Successfully generated {ctx.deps.output_path}"

        # Run the agent
        system = await test_system
        deps = ReadmeTestDeps(orchestrator=system['orchestrator'])
        result = await agent.run("Generate a new readme.test.md file", deps=deps)

        # Verify results
        assert result.data is True
        assert os.path.exists("readme.test.md")
        
        # Verify content
        with open("readme.test.md") as f:
            content = f.read()
            assert "# AI/ML GitHub Repository List" in content
            assert "ml-project" in content.lower()
            assert "machine learning" in content.lower()
            # Verify summary information is included
            assert "primary purpose" in content.lower()
            assert "key technologies" in content.lower()
            assert "target users" in content.lower()

        # Note: Leaving file for inspection
        # To clean up manually: rm readme.test.md

    async def test_repository_processing(self, test_system):
        """Test complete repository processing pipeline."""
        system = await test_system
        
        # Mock newsletter content
        newsletter_content = """
        Check out this new ML framework:
        https://github.com/test/ml-project
        """
        
        # Process through pipeline
        result = await system['orchestrator'].process_repository(
            "https://github.com/test/ml-project",
            newsletter_content,
            "test_email_123"
        )
        
        assert result is not None
        assert "vector_id" in result
        assert "summary" in result
        
        # Verify summary structure
        summary = result["summary"]
        assert "primary_purpose" in summary
        assert "key_technologies" in summary
        assert "target_users" in summary
        assert "main_features" in summary
        assert "technical_domain" in summary
        
        # Verify metadata
        metadata = result["metadata"]
        assert metadata["language"] == "Python"
        assert "machine-learning" in metadata["topics"]
        assert metadata["stars"] == 1000
        assert metadata["forks"] == 500
