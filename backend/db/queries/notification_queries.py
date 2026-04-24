"""
MongoDB queries for the notifications collection.
"""
from database import notifications_col
from bson import ObjectId
from datetime import datetime


async def create_notification(
    type_: str,
    from_user_id: ObjectId,
    to_user_id: ObjectId,
    message: str,
    ref_id: ObjectId = None
):
    doc = {
        "type": type_,
        "from_user_id": from_user_id,
        "to_user_id": to_user_id,
        "message": message,
        "ref_id": ref_id,
        "read": False,
        "created_at": datetime.utcnow(),
    }
    await notifications_col.insert_one(doc)


async def get_notifications_for_user(user_id: ObjectId, limit: int = 50) -> list:
    """
    Return notifications enriched with the sender's name and avatar
    via $lookup, newest first.
    """
    pipeline = [
        {"$match": {"to_user_id": user_id}},
        {"$sort": {"created_at": -1}},
        {"$limit": limit},
        {"$lookup": {
            "from": "users",
            "localField": "from_user_id",
            "foreignField": "_id",
            "as": "from_user"
        }},
        {"$unwind": {"path": "$from_user", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 1,
            "type": 1,
            "message": 1,
            "ref_id": 1,
            "read": 1,
            "created_at": 1,
            "from_user._id": 1,
            "from_user.name": 1,
            "from_user.avatar": 1,
        }}
    ]
    cursor = notifications_col.aggregate(pipeline)
    return [n async for n in cursor]


async def mark_notification_read(notif_id: str, user_id: ObjectId):
    await notifications_col.update_one(
        {"_id": ObjectId(notif_id), "to_user_id": user_id},
        {"$set": {"read": True}}
    )


async def mark_all_read(user_id: ObjectId):
    await notifications_col.update_many(
        {"to_user_id": user_id, "read": False},
        {"$set": {"read": True}}
    )


async def get_unread_count(user_id: ObjectId) -> int:
    return await notifications_col.count_documents(
        {"to_user_id": user_id, "read": False}
    )
