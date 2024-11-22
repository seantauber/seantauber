"""
Repository Details Model

This model follows OpenAI's structured output schema requirements:
https://platform.openai.com/docs/guides/structured-outputs

Supported Types:
- String
- Number (includes float)
- Boolean
- Integer
- Object
- Array
- Enum
- anyOf

Key Requirements:
1. Root level must be an object
2. No default values in schema
3. No field validations in schema (min, max, etc)
4. Validation must be done at runtime

Note: While Pydantic supports advanced features like computed fields and 
field validations, we must keep the schema simple for OpenAI compatibility.
Runtime validation is handled through validators and the is_complete method.
"""

from pydantic import BaseModel, computed_field, validator
from typing import List, Optional

class RepoDetails(BaseModel):
    # Required string fields
    name: str
    full_name: str
    html_url: str
    default_branch: str
    activity_level: str  # Enum validated at runtime: Low, Medium, High
    relevance: str      # Enum validated at runtime: Low, Medium, High
    
    # Optional string fields
    description: Optional[str]
    language: Optional[str]
    
    # Required integer fields
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    watchers_count: int
    
    # Required float field
    star_growth_rate: float
    
    # Required string fields for dates
    updated_at: str
    created_at: str
    
    # Array of strings (no default value)
    topics: List[str]

    @computed_field
    @property
    def id(self) -> str:
        """Unique identifier for the repository"""
        return self.full_name

    @validator("activity_level")
    def validate_activity_level(cls, v):
        allowed = ["Low", "Medium", "High"]
        if v not in allowed:
            raise ValueError(f"activity_level must be one of {allowed}")
        return v

    @validator("relevance")
    def validate_relevance(cls, v):
        allowed = ["Low", "Medium", "High"]
        if v not in allowed:
            raise ValueError(f"relevance must be one of {allowed}")
        return v

    def is_complete(self) -> bool:
        """
        Validates that all required fields are present and valid.
        This runtime validation supplements the basic schema validation.
        """
        try:
            return bool(
                # Required strings must be non-empty
                self.name and
                self.full_name and
                self.html_url and
                
                # Numeric fields must be non-negative
                isinstance(self.stargazers_count, int) and self.stargazers_count >= 0 and
                isinstance(self.forks_count, int) and self.forks_count >= 0 and
                isinstance(self.watchers_count, int) and self.watchers_count >= 0 and
                isinstance(self.open_issues_count, int) and self.open_issues_count >= 0 and
                isinstance(self.star_growth_rate, float) and self.star_growth_rate >= 0 and
                
                # Dates must be present
                self.updated_at and
                self.created_at and
                
                # Enums must have valid values
                self.activity_level in ["Low", "Medium", "High"] and
                self.relevance in ["Low", "Medium", "High"] and

                # Topics must be a list
                isinstance(self.topics, list)
            )
        except Exception:
            return False
