"""
MongoDB queries for the users collection.
"""
from database import users_col
from bson import ObjectId
from datetime import datetime


async def create_user(data: dict) -> str:
    result = await users_col.insert_one(data)
    return str(result.inserted_id)


async def find_user_by_email(email: str):
    return await users_col.find_one({"email": email})


async def find_user_by_id(user_id: str):
    return await users_col.find_one({"_id": ObjectId(user_id)})


async def update_user(user_id: str, updates: dict):
    await users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": updates}
    )
    return await find_user_by_id(user_id)


async def search_users(query: str, limit: int = 20):
    filter_ = {"name": {"$regex": query, "$options": "i"}} if query else {}
    cursor = users_col.find(filter_).limit(limit)
    return [u async for u in cursor]


async def add_connection(user_id: str, target_id: str):
    """Add each user to the other's connection list and increment counter."""
    await users_col.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$addToSet": {"connection_ids": ObjectId(target_id)},
            "$inc": {"connections": 1}
        }
    )
    await users_col.update_one(
        {"_id": ObjectId(target_id)},
        {
            "$addToSet": {"connection_ids": ObjectId(user_id)},
            "$inc": {"connections": 1}
        }
    )


async def is_connected(user_id: str, target_id: str) -> bool:
    user = await find_user_by_id(user_id)
    return ObjectId(target_id) in user.get("connection_ids", [])


async def increment_referral_given(user_id: str):
    await users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"referral_given": 1}}
    )


async def increment_referral_received(user_id: str):
    await users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"referral_received": 1}}
    )
