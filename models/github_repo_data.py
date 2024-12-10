from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional, Any

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

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class TrendingMetrics(BaseModel):
    """Metrics for trending repositories"""
    recent_stars: int
    recent_forks: int
    active_issues: int

class CombinedRepoData(GitHubRepoData):
    """Combined repository data with source and optional trending metrics"""
    source: str  # "starred", "trending", or "both"
    trending_metrics: Optional[TrendingMetrics] = None

class StarredReposOutput(BaseModel):
    """Output model for starred repositories"""
    repositories: List[GitHubRepoData]

class TrendingReposOutput(BaseModel):
    """Output model for trending repositories"""
    repositories: List[GitHubRepoData]

class CombinedReposOutput(BaseModel):
    """Output model for combined repositories"""
    repositories: List[CombinedRepoData]

class AnalyzedRepoData(BaseModel):
    """Repository data with analysis results"""
    repo_data: CombinedRepoData
    quality_score: float
    category: str
    subcategory: str
    include: bool
    justification: str

class AnalyzedReposOutput(BaseModel):
    """Output model for analyzed repositories"""
    repositories: List[AnalyzedRepoData]

class StaticSection(BaseModel):
    """Model for a static section in the README"""
    header: str
    content: List[str] | str

class ReadmeStructure(BaseModel):
    """Structure of the README file"""
    title: str
    introduction: str
    static_sections: Dict[str, StaticSection]
    footer: str

    class Config:
        extra = "allow"  # Allow additional fields in the JSON
