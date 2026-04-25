from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ── Register ──────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    name: str                        # "FirstName LastName" combined
    email: EmailStr
    password: str
    username: Optional[str] = None   # auto-generated on frontend, sent here
    mobile: Optional[str] = None     # from mobile field on register screen
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[List[str]] = []
    avatar: Optional[str] = None


# ── Username suggestion ───────────────────────────────────────────────────────
class UsernameSuggestRequest(BaseModel):
    first_name: str
    last_name: str


# ── Login ─────────────────────────────────────────────────────────────────────
class UserLogin(BaseModel):
    email: str       # accepts email OR mobile number
    password: str


# ── Forgot password ───────────────────────────────────────────────────────────
class ForgotPasswordRequest(BaseModel):
    identifier: str  # email OR mobile


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str
    confirm_password: str


# ── Update profile ────────────────────────────────────────────────────────────
class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[List[str]] = None
    avatar: Optional[str] = None
    mobile: Optional[str] = None
