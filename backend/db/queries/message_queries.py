"""
MongoDB queries for messages and chats collections.
"""
import database
from bson import ObjectId
from datetime import datetime


def _chat_id(a: ObjectId, b: ObjectId) -> str:
    """Deterministic chat ID — same for both participants."""
    ids = sorted([str(a), str(b)])
    return f"{ids[0]}_{ids[1]}"


async def send_message(sender_id: ObjectId, receiver_id: ObjectId, text: str) -> str:
    chat_id = _chat_id(sender_id, receiver_id)

    msg_doc = {
        "chat_id": chat_id,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "text": text,
        "read": False,
        "created_at": datetime.utcnow(),
    }
    result = await database.messages_col.insert_one(msg_doc)

    # upsert the chat summary document
    await database.chats_col.update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "participants": [sender_id, receiver_id],
                "last_message": text,
                "updated_at": datetime.utcnow(),
            },
            "$inc": {"unread_count": 1}
        },
        upsert=True
    )
    return str(result.inserted_id)


async def get_conversation(user_a: ObjectId, user_b: ObjectId) -> list:
    """Return all messages between two users, oldest first."""
    chat_id = _chat_id(user_a, user_b)
    cursor = database.messages_col.find({"chat_id": chat_id}).sort("created_at", 1)
    return [m async for m in cursor]


async def mark_messages_read(user_a: ObjectId, user_b: ObjectId):
    """Mark all unread messages sent TO user_a as read."""
    chat_id = _chat_id(user_a, user_b)
    await database.messages_col.update_many(
        {"chat_id": chat_id, "receiver_id": user_a, "read": False},
        {"$set": {"read": True}}
    )
    await database.chats_col.update_one(
        {"chat_id": chat_id},
        {"$set": {"unread_count": 0}}
    )


async def get_user_chats(user_id: ObjectId) -> list:
    """
    Return all chat threads for a user, enriched with the other
    participant's profile via $lookup.
    """
    pipeline = [
        {"$match": {"participants": user_id}},
        {"$sort": {"updated_at": -1}},
        {"$addFields": {
            "other_user_id": {
                "$arrayElemAt": [
                    {"$filter": {
                        "input": "$participants",
                        "as": "p",
                        "cond": {"$ne": ["$$p", user_id]}
                    }},
                    0
                ]
            }
        }},
        {"$lookup": {
            "from": "users",
            "localField": "other_user_id",
            "foreignField": "_id",
            "as": "other_user"
        }},
        {"$unwind": {"path": "$other_user", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "chat_id": 1, "last_message": 1, "unread_count": 1, "updated_at": 1,
            "other_user._id": 1, "other_user.name": 1,
            "other_user.avatar": 1, "other_user.title": 1, "other_user.company": 1,
        }}
    ]
    cursor = database.chats_col.aggregate(pipeline)
    return [c async for c in cursor]
