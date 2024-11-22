from pydantic import BaseModel
from datetime import datetime
from typing import List

class GitHubRepoData(BaseModel):
    """Streamlined GitHub repository data model with essential fields"""
    full_name: str
    description: str | None
    html_url: str
    stargazers_count: int
    topics: List[str]
    created_at: datetime
    updated_at: datetime
    language: str | None
