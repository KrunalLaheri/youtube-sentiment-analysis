from pydantic import BaseModel
from datetime import datetime

class Comment(BaseModel):
    author: str
    channel_id: str
    text: str
    published_at: datetime
