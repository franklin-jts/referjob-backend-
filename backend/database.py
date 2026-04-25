from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/jobreferalapp")

# Global client — initialized on startup via connect_db()
client: AsyncIOMotorClient = None
db = None

# Collections — assigned after connect_db() is called
users_col         = None
posts_col         = None
messages_col      = None
chats_col         = None
notifications_col = None
referrals_col     = None


async def connect_db():
    """
    Called on FastAPI startup.
    - Creates the MongoDB client
    - Pings the server to confirm the connection works
    - Assigns all collection references
    - Creates indexes for performance
    """
    global client, db
    global users_col, posts_col, messages_col
    global chats_col, notifications_col, referrals_col

    client = AsyncIOMotorClient(MONGO_URI)

    # Ping to verify connection is alive
    await client.admin.command("ping")
    print(f"✅ Connected to MongoDB: {MONGO_URI}")

    db = client.jobreferalapp

    # Assign collections
    users_col         = db["users"]
    posts_col         = db["posts"]
    messages_col      = db["messages"]
    chats_col         = db["chats"]
    notifications_col = db["notifications"]
    referrals_col     = db["referrals"]

    # Create indexes
    await create_indexes()
    print("✅ Indexes ensured")


async def close_db():
    """Called on FastAPI shutdown — closes the MongoDB connection cleanly."""
    global client
    if client:
        client.close()
        print("🔌 MongoDB connection closed")


async def create_indexes():
    """
    Creates all indexes needed for fast queries.
    Uses background=True so it doesn't block the app on startup.
    Safe to call multiple times — MongoDB ignores existing indexes.
    """
    # ── Users ──────────────────────────────────────────────
    await users_col.create_index("email", unique=True)
    await users_col.create_index("mobile", unique=True, sparse=True)
    await users_col.create_index("username", unique=True, sparse=True)
    await users_col.create_index([("name", "text")])          # text search

    # ── Posts ──────────────────────────────────────────────
    await posts_col.create_index([("created_at", -1)])        # feed sort
    await posts_col.create_index("user_id")                   # posts by user

    # ── Messages ───────────────────────────────────────────
    await messages_col.create_index([("chat_id", 1), ("created_at", 1)])  # conversation
    await messages_col.create_index([("receiver_id", 1), ("read", 1)])    # unread

    # ── Chats ──────────────────────────────────────────────
    await chats_col.create_index("chat_id", unique=True)
    await chats_col.create_index("participants")              # inbox lookup

    # ── Referrals ──────────────────────────────────────────
    await referrals_col.create_index("requester_id")
    await referrals_col.create_index("referrer_id")
    await referrals_col.create_index("status")

    # ── Notifications ──────────────────────────────────────
    await notifications_col.create_index([("to_user_id", 1), ("read", 1)])
    await notifications_col.create_index([("created_at", -1)])
