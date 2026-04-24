from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageSend(BaseModel):
    receiver_id: str
    text: str


class MessageOut(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    text: str
    read: bool = False
    created_at: datetime


class ChatOut(BaseModel):
    chat_id: str
    other_user_id: str
    last_message: Optional[str] = None
    unread_count: int = 0
    updated_at: datetime
