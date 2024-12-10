from pydantic_settings import BaseSettings
from pydantic import validator
from typing import Optional
import os

class GitHubConfig(BaseSettings):
    github_username: str
    github_token: str
    
    @validator('github_username')
    def username_must_not_be_empty(cls, v):
        if not v or v.isspace():
            raise ValueError('GitHub username cannot be empty')
        return v
    
    @validator('github_token')
    def token_must_not_be_empty(cls, v):
        if not v or v.isspace():
            raise ValueError('GitHub token cannot be empty')
        return v

class AppConfig(BaseSettings):
    github: GitHubConfig
    openai_api_key: str
    database_url: str = "db/github_repos.db"
    max_workers: int = 4
    batch_size: int = 10
    
    @validator('openai_api_key')
    def openai_key_must_not_be_empty(cls, v):
        if not v or v.isspace():
            raise ValueError('OpenAI API key cannot be empty')
        return v
    
    @classmethod
    def from_env(cls):
        """Create AppConfig from environment variables"""
        # First create GitHub config
        github_config = GitHubConfig(
            github_username=os.getenv('GITHUB_USERNAME', ''),
            github_token=os.getenv('GITHUB_TOKEN', '')
        )
        
        # Create main app config with GitHub config
        return cls(
            github=github_config,
            openai_api_key=os.getenv('OPENAI_API_KEY', ''),
            database_url=os.getenv('DATABASE_URL', 'db/github_repos.db'),
            max_workers=int(os.getenv('MAX_WORKERS', '4')),
            batch_size=int(os.getenv('BATCH_SIZE', '10'))
        )
    
    class Config:
        env_file = ".env"
