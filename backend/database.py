from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/jobreferalapp")

client = AsyncIOMotorClient(MONGO_URI)
db = client.jobreferalapp

# Collections
users_col       = db["users"]
posts_col       = db["posts"]
messages_col    = db["messages"]
chats_col       = db["chats"]
notifications_col = db["notifications"]
referrals_col   = db["referrals"]
