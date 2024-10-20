from pydantic import BaseModel
from typing import List

class CurationDetails(BaseModel):
    tags: List[str]
    popularity_score: float
    trending_score: float
