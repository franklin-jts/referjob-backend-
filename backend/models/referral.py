from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReferralRequest(BaseModel):
    referrer_id: str              # user who will give the referral
    post_id: str                  # the job post being referred for
    resume_url: Optional[str] = None
    note: Optional[str] = None
    # Fields from ReferModal.tsx
    friend_name: Optional[str] = None
    friend_email: Optional[str] = None
    app_username: Optional[str] = None
    mobile_number: Optional[str] = None


class ReferralOut(BaseModel):
    id: str
    requester_id: str
    referrer_id: str
    post_id: str
    resume_url: Optional[str] = None
    note: Optional[str] = None
    friend_name: Optional[str] = None
    friend_email: Optional[str] = None
    app_username: Optional[str] = None
    mobile_number: Optional[str] = None
    status: str = "pending"   # pending | accepted | rejected | submitted
    created_at: datetime
