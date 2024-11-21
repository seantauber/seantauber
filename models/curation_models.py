from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional

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
