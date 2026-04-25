from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import connect_db, close_db
from routes import auth, users, posts, referrals, messages, notifications


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────
    await connect_db()
    yield
    # ── Shutdown ─────────────────────────────────────────
    await close_db()


app = FastAPI(
    title="Job Referral App API",
    description="Backend API for the Job Referral social platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(referrals.router)
app.include_router(messages.router)
app.include_router(notifications.router)


@app.get("/")
async def root():
    return {"message": "Job Referral App API is running"}
