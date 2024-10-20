from pydantic import BaseModel

class EditorNote(BaseModel):
    content: str
