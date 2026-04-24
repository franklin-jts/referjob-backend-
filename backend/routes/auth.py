from fastapi import APIRouter, HTTPException, Depends
from passlib.context import CryptContext
from models.user import UserRegister, UserLogin
from middleware.auth import create_token, get_current_user
from db.queries.user_queries import find_user_by_email, create_user
from datetime import datetime

router = APIRouter(prefix="/api/auth", tags=["Auth"])
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register", status_code=201)
async def register(body: UserRegister):
    if await find_user_by_email(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_doc = {
        "name": body.name,
        "email": body.email,
        "password": pwd_ctx.hash(body.password),
        "title": body.title,
        "company": body.company,
        "location": body.location,
        "bio": body.bio,
        "skills": body.skills or [],
        "avatar": body.avatar,
        "connections": 0,
        "referral_given": 0,
        "referral_received": 0,
        "connection_ids": [],
        "created_at": datetime.utcnow(),
    }
    user_id = await create_user(user_doc)
    token = create_token(user_id)
    return {"token": token, "user_id": user_id}


@router.post("/login")
async def login(body: UserLogin):
    user = await find_user_by_email(body.email)
    if not user or not pwd_ctx.verify(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(str(user["_id"]))
    return {"token": token, "user_id": str(user["_id"])}


@router.get("/me")
async def me(current_user=Depends(get_current_user)):
    """Validate token and return current user — called on app startup."""
    user = dict(current_user)
    user["id"] = str(user.pop("_id"))
    user.pop("password", None)
    user["connection_ids"] = [str(c) for c in user.get("connection_ids", [])]
    return user
