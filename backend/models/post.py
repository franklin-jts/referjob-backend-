from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PostCreate(BaseModel):
    type: str  # "job_post" | "referral_offer"
    company: str
    company_logo: Optional[str] = None
    job_title: str
    location: str
    salary: Optional[str] = None
    experience: Optional[str] = None
    skills: Optional[List[str]] = []
    description: str
    can_refer: bool = False


class PostOut(BaseModel):
    id: str
    type: str
    user_id: str
    company: str
    company_logo: Optional[str] = None
    job_title: str
    location: str
    salary: Optional[str] = None
    experience: Optional[str] = None
    skills: List[str] = []
    description: str
    likes: int = 0
    comments: int = 0
    referrals: int = 0
    can_refer: bool = False
    created_at: datetime


class PostUpdate(BaseModel):
    type: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    company_logo: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    experience: Optional[str] = None
    skills: Optional[List[str]] = None
    description: Optional[str] = None
    can_refer: Optional[bool] = None


class CommentCreate(BaseModel):
    text: str
