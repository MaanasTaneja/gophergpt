from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class UserProfile(BaseModel):
    user_id: str
    name: Optional[str] = None
    major: Optional[str] = None
    year: Optional[str] = None
    preferences: Dict[str, str] = Field(default_factory=dict)
    interests: List[str] = Field(default_factory=list)
    saved_courses: List[str] = Field(default_factory=list)
    recent_topics: List[str] = Field(default_factory=list)
    conversation_summary: str = ""