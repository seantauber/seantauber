"""Configuration management for component tests."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

class TestSettings(BaseSettings):
    """Test configuration settings."""
    
    # Base paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    TEST_DATA_DIR: Path = PROJECT_ROOT / "tests" / "data"
    
    # Gmail API Configuration
    GMAIL_CREDENTIALS_PATH: str
    GMAIL_TOKEN_PATH: str
    
    # GitHub Configuration
    GITHUB_TOKEN: str
    
    # LLM Configuration
    OPENAI_API_KEY: str
    
    # Logfire Configuration
    LOGFIRE_TOKEN: str
    
    # Vector Storage
    VECTOR_STORAGE_PATH: Path = PROJECT_ROOT / "tests" / "vector_storage"
    
    # Database
    TEST_DATABASE_PATH: Path = PROJECT_ROOT / "tests" / "test.db"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Path = PROJECT_ROOT / "tests" / "component_tests.log"
    
    # Test Control
    ENABLE_LIVE_TESTS: bool = True
    MAX_TEST_REPOSITORIES: int = 5
    API_RETRY_ATTEMPTS: int = 3
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env.test"
        env_file_encoding = "utf-8"

def get_test_settings() -> TestSettings:
    """Get test configuration settings.
    
    Returns:
        TestSettings: Configuration settings for tests
        
    Raises:
        ValueError: If required environment variables are missing
    """
    try:
        return TestSettings()
    except Exception as e:
        raise ValueError(
            "Failed to load test settings. Ensure .env.test file exists "
            f"with required configuration: {str(e)}"
        )

# Create test directories if they don't exist
def setup_test_environment() -> None:
    """Create necessary test directories and initialize environment."""
    settings = get_test_settings()
    
    # Create test directories
    settings.TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.VECTOR_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    
    # Verify credentials exist
    if not os.path.exists(settings.GMAIL_CREDENTIALS_PATH):
        raise FileNotFoundError(
            f"Gmail credentials not found at {settings.GMAIL_CREDENTIALS_PATH}"
        )
    
    if not os.path.exists(settings.GMAIL_TOKEN_PATH):
        raise FileNotFoundError(
            f"Gmail token not found at {settings.GMAIL_TOKEN_PATH}"
        )

def get_test_database_url() -> str:
    """Get SQLite database URL for tests.
    
    Returns:
        str: Database URL for test database
    """
    settings = get_test_settings()
    return f"sqlite:///{settings.TEST_DATABASE_PATH}"

# Example .env.test file template
ENV_TEMPLATE = """# Gmail API Configuration
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
GMAIL_TOKEN_PATH=/path/to/token.json

# GitHub Configuration
GITHUB_TOKEN=your_github_token

# LLM Configuration
OPENAI_API_KEY=your_openai_key

# Logfire Configuration
LOGFIRE_TOKEN=your_logfire_token

# Test Control
ENABLE_LIVE_TESTS=true
MAX_TEST_REPOSITORIES=5
API_RETRY_ATTEMPTS=3

# Logging
LOG_LEVEL=INFO
"""

def create_env_template() -> None:
    """Create a template .env.test file if it doesn't exist."""
    env_file = Path(".env.test")
    if not env_file.exists():
        env_file.write_text(ENV_TEMPLATE)
        print(f"Created template .env.test file at {env_file.absolute()}")
        print("Please update with your actual configuration values")

if __name__ == "__main__":
    # Create template .env.test file when run directly
    create_env_template()
