from pydantic import BaseModel, EmailStr
from typing import Optional, List


# ── Register ──────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    username: Optional[str] = None
    mobile: Optional[str] = None
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
    email: str
    password: str


# ── Forgot / Reset password ───────────────────────────────────────────────────
class ForgotPasswordRequest(BaseModel):
    identifier: str

class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str
    confirm_password: str


# ── Profile sub-models ────────────────────────────────────────────────────────
class ExperienceItem(BaseModel):
    employer_name: str
    role: str
    start_date: str
    end_date: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None


class EducationItem(BaseModel):
    college_name: str
    degree: str
    field_of_study: Optional[str] = None
    start_year: str
    end_year: Optional[str] = None
    cgpa: Optional[str] = None


class CertificationItem(BaseModel):
    name: str
    issuer: str
    year: Optional[str] = None


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
    banner: Optional[str] = None
    mobile: Optional[str] = None
    experience: Optional[List[ExperienceItem]] = None
    education: Optional[List[EducationItem]] = None
    certifications: Optional[List[CertificationItem]] = None
    cv_url: Optional[str] = None
    cv_filename: Optional[str] = None
    ats_score: Optional[int] = None
    ats_suggestions: Optional[List[str]] = None


# ── Preferences ───────────────────────────────────────────────────────────────
class UserPreferences(BaseModel):
    push_notifications: Optional[bool] = None
    email_alerts:       Optional[bool] = None
    referral_alerts:    Optional[bool] = None
    job_alerts:         Optional[bool] = None
    profile_visible:    Optional[bool] = None
    show_connections:   Optional[bool] = None
