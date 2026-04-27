"""
MongoDB queries for the users collection.
"""
import database
from bson import ObjectId


async def get_next_user_number() -> int:
    """Auto-increment counter for regular user IDs (1, 2, 3 ...)"""
    result = await database.db["counters"].find_one_and_update(
        {"_id": "user_seq"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    return result["seq"]


async def get_next_admin_number() -> str:
    """Auto-increment counter for admin IDs (jts001, jts002 ...)"""
    result = await database.db["counters"].find_one_and_update(
        {"_id": "admin_seq"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    return f"jts{result['seq']:03d}"


async def create_user(data: dict) -> str:
    result = await database.users_col.insert_one(data)
    return str(result.inserted_id)


async def find_user_by_email(email: str):
    return await database.users_col.find_one({"email": email})


async def find_user_by_mobile(mobile: str):
    return await database.users_col.find_one({"mobile": mobile})


async def find_user_by_email_or_mobile(identifier: str):
    """Used for login and forgot password — accepts email or mobile."""
    return await database.users_col.find_one({
        "$or": [{"email": identifier}, {"mobile": identifier}]
    })


async def find_user_by_username(username: str):
    return await database.users_col.find_one({"username": username})


async def find_user_by_reset_token(token: str):
    return await database.users_col.find_one({"reset_token": token})


async def find_user_by_id(user_id: str):
    return await database.users_col.find_one({"_id": ObjectId(user_id)})


async def update_user(user_id: str, updates: dict):
    await database.users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": updates}
    )
    return await find_user_by_id(user_id)


async def search_users(query: str, limit: int = 20):
    filter_ = {"name": {"$regex": query, "$options": "i"}} if query else {}
    cursor = database.users_col.find(filter_).limit(limit)
    return [u async for u in cursor]


async def add_connection(user_id: str, target_id: str):
    await database.users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$addToSet": {"connection_ids": ObjectId(target_id)}, "$inc": {"connections": 1}}
    )
    await database.users_col.update_one(
        {"_id": ObjectId(target_id)},
        {"$addToSet": {"connection_ids": ObjectId(user_id)}, "$inc": {"connections": 1}}
    )


async def is_connected(user_id: str, target_id: str) -> bool:
    user = await find_user_by_id(user_id)
    return ObjectId(target_id) in user.get("connection_ids", [])


async def increment_referral_given(user_id: str):
    await database.users_col.update_one(
        {"_id": ObjectId(user_id)}, {"$inc": {"referral_given": 1}}
    )


async def increment_referral_received(user_id: str):
    await database.users_col.update_one(
        {"_id": ObjectId(user_id)}, {"$inc": {"referral_received": 1}}
    )
