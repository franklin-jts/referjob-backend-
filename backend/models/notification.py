from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationOut(BaseModel):
    id: str
    type: str   # referral_request | like | comment | referral_accepted | connection
    from_user_id: str
    to_user_id: str
    message: str
    ref_id: Optional[str] = None   # post_id or referral_id
    read: bool = False
    created_at: datetime
