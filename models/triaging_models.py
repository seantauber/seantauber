from pydantic import BaseModel
from typing import List

class TriagingResponse(BaseModel):
    agents: List[str]
    query: str
