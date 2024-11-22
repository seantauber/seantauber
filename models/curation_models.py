from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime

class CategoryHierarchy(BaseModel):
    """Represents a hierarchical category structure with confidence scoring"""
    main_category: str = Field(..., description="Primary category classification")
    subcategory: Optional[str] = Field(None, description="Optional subcategory for more specific classification")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the categorization")
    reasoning: str = Field(..., min_length=1, description="Explanation for the categorization decision")

class CurationDetails(BaseModel):
    """Legacy model maintained for backward compatibility"""
    tags: List[str]
    popularity_score: float
    trending_score: float

class EnhancedCurationDetails(CurationDetails):
    """Enhanced curation details with hierarchical categorization and additional metadata"""
    categories: List[CategoryHierarchy] = Field(..., min_length=1, description="Hierarchical category classifications")
    related_repos: List[str] = Field(default_factory=list, description="List of related repository IDs")
    consensus_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Data from the multi-agent consensus process"
    )
    version: str = Field(
        default="1.0.0",
        pattern=r"^\d+\.\d+\.\d+$",
        description="Version of the curation model used"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tags": ["machine-learning", "python"],
                "popularity_score": 0.85,
                "trending_score": 0.92,
                "categories": [{
                    "main_category": "AI/ML",
                    "subcategory": "Deep Learning",
                    "confidence": 0.95,
                    "reasoning": "Repository contains deep learning frameworks and neural network implementations"
                }],
                "related_repos": ["repo1", "repo2"],
                "consensus_data": {
                    "agent_decisions": {
                        "category_agent": "AI/ML",
                        "review_agent": "AI/ML",
                        "validation_agent": "AI/ML"
                    },
                    "confidence_scores": {
                        "category_agent": 0.9,
                        "review_agent": 0.95,
                        "validation_agent": 0.92
                    }
                },
                "version": "1.0.0"
            }
        }
    )

class HistoricalDecision(BaseModel):
    """Represents a single historical categorization decision"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the decision was made")
    categories: List[CategoryHierarchy] = Field(..., description="Categories assigned at this point")
    agent_decisions: Dict[str, Any] = Field(..., description="Individual agent decisions and confidence scores")
    version: str = Field(..., description="Model version used for this decision")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the decision context"
    )

class RepositoryHistory(BaseModel):
    """Tracks the complete history of categorization decisions for a repository"""
    repository_id: str = Field(..., description="Unique identifier for the repository")
    decisions: List[HistoricalDecision] = Field(
        default_factory=list,
        description="Chronological list of categorization decisions"
    )
    latest_decision: Optional[HistoricalDecision] = Field(
        None,
        description="Most recent categorization decision"
    )
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Statistical analysis of historical decisions"
    )

    def add_decision(self, decision: HistoricalDecision):
        """Add a new decision to the history and update statistics"""
        self.decisions.append(decision)
        self.latest_decision = decision
        self._update_statistics()

    def _update_statistics(self):
        """Update statistical analysis of historical decisions"""
        # Initialize default values
        self.statistics = {
            "total_decisions": 0,
            "category_stability": {},
            "confidence_trends": {},
            "last_updated": datetime.utcnow()
        }

        if not self.decisions:
            return

        # Calculate category stability
        category_counts: Dict[str, int] = {}
        for decision in self.decisions:
            for category in decision.categories:
                key = f"{category.main_category}:{category.subcategory}"
                category_counts[key] = category_counts.get(key, 0) + 1

        total_decisions = len(self.decisions)
        self.statistics["total_decisions"] = total_decisions
        
        category_stability = {
            category: count / total_decisions
            for category, count in category_counts.items()
        }
        self.statistics["category_stability"] = category_stability

        # Calculate average confidence trends
        confidence_trends = {}
        for decision in self.decisions:
            for agent, data in decision.agent_decisions.items():
                if isinstance(data, dict) and "confidence" in data:
                    if agent not in confidence_trends:
                        confidence_trends[agent] = []
                    confidence_trends[agent].append(data["confidence"])

        avg_confidence_trends = {
            agent: sum(scores) / len(scores)
            for agent, scores in confidence_trends.items()
        }
        self.statistics["confidence_trends"] = avg_confidence_trends
