from pydantic import BaseModel
from typing import List

class RepoDetails(BaseModel):
    name: str
    full_name: str
    description: str
    html_url: str
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    watchers_count: int
    language: str
    updated_at: str
    created_at: str
    topics: List[str]
    default_branch: str
    star_growth_rate: float
    activity_level: str
    relevance: str
