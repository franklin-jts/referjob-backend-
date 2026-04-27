from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StoryCreate(BaseModel):
    image_url: str
    caption: Optional[str] = None
    link_url: Optional[str] = None
    expires_at: Optional[datetime] = None
