"""Global test configuration."""

import os
import pytest
import logfire
from pathlib import Path
from dotenv import load_dotenv

def pytest_configure(config):
    """Configure test environment."""
    # Load environment variables from .env.test
    env_file = Path(__file__).parent.parent / '.env.test'
    if env_file.exists():
        load_dotenv(env_file)
    else:
        raise RuntimeError(".env.test file not found")

    # Configure Logfire with token from environment
    logfire_token = os.getenv('LOGFIRE_TOKEN')
    if not logfire_token:
        raise RuntimeError("LOGFIRE_TOKEN not found in environment")

    logfire.configure(
        service_name="github-genai-list-test",
        service_version="0.1.0",
        environment="test",
        token=logfire_token
    )
