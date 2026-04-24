from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[List[str]] = []
    avatar: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[List[str]] = None
    avatar: Optional[str] = None


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    skills: List[str] = []
    avatar: Optional[str] = None
    connections: int = 0
    referral_given: int = 0
    referral_received: int = 0
    created_at: datetime
