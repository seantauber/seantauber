"""Models for flow state management"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from models.github_repo_data import GitHubRepoData

class RepoProcessingState(BaseModel):
    """State for tracking repo processing progress"""
    total_repos: int = 0
    processed_repos: int = 0
    analyzed_repos: int = 0
    failed_repos: int = 0
    errors: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)

class RepoCategorization(BaseModel):
    """Model for repo categorization results"""
    category: str
    subcategory: Optional[str] = None
    confidence: float
    reasoning: str

class RepoAnalysis(BaseModel):
    """Model for analyzed repo data"""
    repo_data: GitHubRepoData
    categorization: RepoCategorization
    quality_score: float
    relevance_score: float
    analysis_date: datetime = Field(default_factory=datetime.now)

class ReadmeState(BaseModel):
    """State for README generation"""
    categories: Dict[str, Dict[str, List[str]]] = Field(default_factory=dict)
    toc_items: List[str] = Field(default_factory=list)
    content: str = ""
    last_updated: datetime = Field(default_factory=datetime.now)

class FlowState(BaseModel):
    """Main state model for the GitHub GenAI List flow"""
    # Raw data
    raw_repos: List[GitHubRepoData] = Field(default_factory=list)
    
    # Processing state
    processing: RepoProcessingState = Field(default_factory=RepoProcessingState)
    
    # Analysis results
    analyzed_repos: List[RepoAnalysis] = Field(default_factory=list)
    
    # README state
    readme: ReadmeState = Field(default_factory=ReadmeState)
    
    # Flow metadata
    flow_start_time: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def update_processing_state(self, processed: int = 0, analyzed: int = 0, failed: int = 0, error: Optional[str] = None):
        """Update processing state with new counts"""
        self.processing.processed_repos += processed
        self.processing.analyzed_repos += analyzed
        self.processing.failed_repos += failed
        if error:
            self.processing.errors.append(error)
        self.processing.last_updated = datetime.now()
        self.last_updated = datetime.now()
    
    def add_raw_repos(self, repos: List[GitHubRepoData]):
        """Add raw repos to state"""
        self.raw_repos.extend(repos)
        self.processing.total_repos = len(self.raw_repos)
        self.last_updated = datetime.now()
    
    def add_analyzed_repo(self, analysis: RepoAnalysis):
        """Add analyzed repo to state"""
        self.analyzed_repos.append(analysis)
        self.update_processing_state(analyzed=1)
    
    def update_readme_state(self, categories: Dict[str, Dict[str, List[str]]], content: str):
        """Update README state with new content"""
        self.readme.categories = categories
        self.readme.content = content
        self.readme.last_updated = datetime.now()
        self.last_updated = datetime.now()
    
    def get_progress(self) -> Dict:
        """Get current processing progress"""
        return {
            'total_repos': self.processing.total_repos,
            'processed': self.processing.processed_repos,
            'analyzed': self.processing.analyzed_repos,
            'failed': self.processing.failed_repos,
            'errors': len(self.processing.errors),
            'categories': len(self.readme.categories),
            'last_updated': self.last_updated.isoformat()
        }
