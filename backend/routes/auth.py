import re
import random
import string
import bcrypt
from fastapi import APIRouter, HTTPException, Depends
from models.user import (
    UserRegister, UserLogin, UsernameSuggestRequest,
    ForgotPasswordRequest, ResetPasswordRequest
)
from middleware.auth import create_token, get_current_user
from db.queries.user_queries import (
    find_user_by_email, find_user_by_mobile,
    find_user_by_email_or_mobile, find_user_by_username,
    find_user_by_reset_token, create_user, update_user,
    get_next_user_number, get_next_admin_number
)
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _generate_username(name: str) -> str:
    """
    Auto-generate username from full name.
    Format: firstnamelastinitial + symbol + number
    e.g.  arjuns#4821  |  priya_n@392
    """
    parts = name.strip().split()
    first = re.sub(r"[^a-z]", "", parts[0].lower()) if parts else "user"
    last_initial = re.sub(r"[^a-z]", "", parts[-1].lower())[:1] if len(parts) > 1 else ""
    symbol = random.choice(["#", "_", ".", "@"])
    number = random.randint(100, 9999)
    return f"{first}{last_initial}{symbol}{number}"


def _generate_reset_token() -> str:
    """6-digit OTP for password reset."""
    return "".join(random.choices(string.digits, k=6))


def _fmt_user(user: dict) -> dict:
    user = dict(user)
    user["id"] = str(user.pop("_id"))
    user.pop("password", None)
    user.pop("reset_token", None)
    user.pop("reset_token_expiry", None)
    user["connection_ids"] = [str(c) for c in user.get("connection_ids", [])]
    # expose readable user_id (1, 2, 3 for users / jts001 for admins)
    user.setdefault("user_id", user["id"])
    return user


# ── Suggest usernames ─────────────────────────────────────────────────────────

@router.post("/suggest-username")
async def suggest_username(body: UsernameSuggestRequest):
    """
    Called when user types first + last name on register screen.
    Returns 3 unique auto-generated username suggestions.
    """
    suggestions = []
    attempts = 0
    full_name = f"{body.first_name} {body.last_name}"
    while len(suggestions) < 3 and attempts < 20:
        candidate = _generate_username(full_name)
        if not await find_user_by_username(candidate):
            suggestions.append(candidate)
        attempts += 1
    return {"suggestions": suggestions}


# ── Check username availability ───────────────────────────────────────────────

@router.get("/check-username/{username}")
async def check_username(username: str):
    """Check if a manually entered username is already taken."""
    existing = await find_user_by_username(username)
    return {"available": existing is None}


# ── Register ──────────────────────────────────────────────────────────────────

@router.post("/register", status_code=201)
async def register(body: UserRegister):
    """
    Accepts exactly what the frontend RegisterView sends:
      name, email, password, username (optional), mobile (optional),
      title, company, location, bio, skills, avatar
    """
    # duplicate email check
    if await find_user_by_email(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # duplicate mobile check (only if provided)
    if body.mobile and await find_user_by_mobile(body.mobile):
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    # auto-generate username if frontend didn't send one
    username = body.username
    if not username:
        username = _generate_username(body.name)
        # ensure uniqueness
        while await find_user_by_username(username):
            username = _generate_username(body.name)

    # duplicate username check
    if await find_user_by_username(username):
        raise HTTPException(status_code=400, detail="Username already taken")

    user_doc = {
        "name":       body.name,
        "email":      body.email,
        "password":   _hash(body.password),
        "username":   username,
        "mobile":     body.mobile or "",
        "title":      body.title or "",
        "company":    body.company or "",
        "location":   body.location or "",
        "bio":        body.bio or "",
        "skills":     body.skills or [],
        "avatar":     body.avatar or f"https://i.pravatar.cc/150?u={body.email}",
        "connections":       0,
        "referral_given":    0,
        "referral_received": 0,
        "connection_ids":    [],
        "role":              "user",
        "user_id":           await get_next_user_number(),
        "created_at":        datetime.utcnow(),
    }

    user_id = await create_user(user_doc)
    token   = create_token(user_id)

    return {
        "token":    token,
        "user_id":  user_id,
        "username": username,
        "name":     body.name,
    }


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login")
async def login(body: UserLogin):
    """Login with email OR mobile number + password."""
    user = await find_user_by_email_or_mobile(body.email)
    if not user or not _verify(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(str(user["_id"]))
    return {
        "token":    token,
        "user_id":  str(user["_id"]),
        "username": user.get("username"),
        "name":     user.get("name"),
    }


# ── Forgot password ───────────────────────────────────────────────────────────

@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    """
    User enters registered email OR mobile.
    Generates a 6-digit OTP valid for 15 minutes.
    Returns OTP directly for now — in production send via SMS/email.
    """
    user = await find_user_by_email_or_mobile(body.identifier)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="No account found with that email or mobile number"
        )

    token  = _generate_reset_token()
    expiry = datetime.utcnow() + timedelta(minutes=15)

    await update_user(str(user["_id"]), {
        "reset_token":        token,
        "reset_token_expiry": expiry,
    })

    # TODO: send token via SMS/email in production
    return {
        "message":          "Reset OTP sent successfully",
        "reset_token":      token,   # remove in production
        "expires_in_minutes": 15,
    }


# ── Reset password ────────────────────────────────────────────────────────────

@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest):
    """User submits OTP + new password."""
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user = await find_user_by_reset_token(body.reset_token)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    if datetime.utcnow() > user.get("reset_token_expiry", datetime.utcnow()):
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new one")

    await update_user(str(user["_id"]), {
        "password":           _hash(body.new_password),
        "reset_token":        None,
        "reset_token_expiry": None,
    })
    return {"message": "Password reset successfully. Please log in."}


# ── Get current user (session restore) ───────────────────────────────────────

@router.get("/me")
async def me(current_user=Depends(get_current_user)):
    """Validate token on app startup and return user profile."""
    return _fmt_user(current_user)


# ── Admin Register ────────────────────────────────────────────────────────────

ADMIN_SECRET = "jts-admin-2024"   # change this in production / move to .env

@router.post("/admin/register", status_code=201)
async def admin_register(body: UserRegister, secret: str):
    """
    Register an admin user. Requires secret key as query param.
    POST /api/auth/admin/register?secret=jts-admin-2024
    Assigns admin_id like jts001, jts002 ...
    """
    if secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    if await find_user_by_email(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    username = body.username or _generate_username(body.name)
    while await find_user_by_username(username):
        username = _generate_username(body.name)

    admin_id = await get_next_admin_number()

    user_doc = {
        "name":       body.name,
        "email":      body.email,
        "password":   _hash(body.password),
        "username":   username,
        "mobile":     body.mobile or "",
        "title":      body.title or "Admin",
        "company":    body.company or "JTS",
        "location":   body.location or "",
        "bio":        body.bio or "",
        "skills":     body.skills or [],
        "avatar":     body.avatar or f"https://i.pravatar.cc/150?u={body.email}",
        "connections":       0,
        "referral_given":    0,
        "referral_received": 0,
        "connection_ids":    [],
        "role":              "admin",
        "user_id":           admin_id,
        "created_at":        datetime.utcnow(),
    }

    mongo_id = await create_user(user_doc)
    token    = create_token(mongo_id)

    return {
        "token":    token,
        "user_id":  admin_id,
        "username": username,
        "name":     body.name,
        "role":     "admin",
    }
