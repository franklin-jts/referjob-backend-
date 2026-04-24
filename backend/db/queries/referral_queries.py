"""
MongoDB queries for the referrals collection.
"""
from database import referrals_col
from bson import ObjectId
from datetime import datetime


async def create_referral(data: dict) -> str:
    result = await referrals_col.insert_one(data)
    return str(result.inserted_id)


async def find_pending_referral(requester_id: ObjectId, referrer_id: str, post_id: str):
    """Check if a pending request already exists to avoid duplicates."""
    return await referrals_col.find_one({
        "requester_id": requester_id,
        "referrer_id": ObjectId(referrer_id),
        "post_id": ObjectId(post_id),
        "status": "pending"
    })


async def get_referral_by_id(referral_id: str):
    return await referrals_col.find_one({"_id": ObjectId(referral_id)})


async def get_my_requests(requester_id: ObjectId) -> list:
    """All referrals the current user has requested, with post & referrer info."""
    pipeline = [
        {"$match": {"requester_id": requester_id}},
        {"$sort": {"created_at": -1}},
        {"$lookup": {
            "from": "posts",
            "localField": "post_id",
            "foreignField": "_id",
            "as": "post"
        }},
        {"$unwind": {"path": "$post", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "users",
            "localField": "referrer_id",
            "foreignField": "_id",
            "as": "referrer"
        }},
        {"$unwind": {"path": "$referrer", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 1, "status": 1, "resume_url": 1, "note": 1, "created_at": 1,
            "post.job_title": 1, "post.company": 1,
            "referrer.name": 1, "referrer.avatar": 1, "referrer.company": 1,
        }}
    ]
    cursor = referrals_col.aggregate(pipeline)
    return [r async for r in cursor]


async def get_my_referrals(referrer_id: ObjectId) -> list:
    """All referral requests assigned to the current user to action."""
    pipeline = [
        {"$match": {"referrer_id": referrer_id}},
        {"$sort": {"created_at": -1}},
        {"$lookup": {
            "from": "posts",
            "localField": "post_id",
            "foreignField": "_id",
            "as": "post"
        }},
        {"$unwind": {"path": "$post", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "users",
            "localField": "requester_id",
            "foreignField": "_id",
            "as": "requester"
        }},
        {"$unwind": {"path": "$requester", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 1, "status": 1, "resume_url": 1, "note": 1, "created_at": 1,
            "post.job_title": 1, "post.company": 1,
            "requester.name": 1, "requester.avatar": 1, "requester.title": 1,
        }}
    ]
    cursor = referrals_col.aggregate(pipeline)
    return [r async for r in cursor]


async def update_referral_status(referral_id: str, status: str):
    await referrals_col.update_one(
        {"_id": ObjectId(referral_id)},
        {"$set": {"status": status, "updated_at": datetime.utcnow()}}
    )
