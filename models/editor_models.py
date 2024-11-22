from pydantic import BaseModel, HttpUrl, validator
from typing import List, Dict, Optional

class EditorNote(BaseModel):
    content: str

class CategoryAssignment(BaseModel):
    category: str

class Repository(BaseModel):
    name: str
    url: HttpUrl
    description: Optional[str] = "No description available"

    @validator("description", pre=True, always=True)
    def default_description(cls, v):
        return v or "No description available"

class Category(BaseModel):
    name: str
    repositories: List[Repository]

class ExtractedReadme(BaseModel):
    categories: List[Category]

    @classmethod
    def from_dict(cls, data: Dict) -> "ExtractedReadme":
        categories = [
            Category(
                name=category_name,
                repositories=[
                    Repository(name=repo["name"], url=repo["url"], description=repo.get("description"))
                    for repo in repos
                ],
            )
            for category_name, repos in data.items()
        ]
        return cls(categories=categories)
