"""
MongoDB queries for the posts collection.
"""
from database import posts_col
from bson import ObjectId
from datetime import datetime


async def create_post(data: dict) -> str:
    result = await posts_col.insert_one(data)
    return str(result.inserted_id)


async def get_feed(skip: int = 0, limit: int = 20) -> list:
    """Return posts sorted newest first with author info joined."""
    pipeline = [
        {"$sort": {"created_at": -1}},
        {"$skip": skip},
        {"$limit": limit},
        # join author details from users collection
        {"$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "_id",
            "as": "author"
        }},
        {"$unwind": {"path": "$author", "preserveNullAndEmptyArrays": True}},
        # shape the output
        {"$project": {
            "_id": 1,
            "type": 1,
            "company": 1,
            "company_logo": 1,
            "job_title": 1,
            "location": 1,
            "salary": 1,
            "experience": 1,
            "skills": 1,
            "description": 1,
            "likes": 1,
            "referrals": 1,
            "can_refer": 1,
            "created_at": 1,
            "comments_count": 1,
            "author.name": 1,
            "author.avatar": 1,
            "author.title": 1,
            "author.company": 1,
        }}
    ]
    cursor = posts_col.aggregate(pipeline)
    return [p async for p in cursor]


async def get_post_by_id(post_id: str):
    pipeline = [
        {"$match": {"_id": ObjectId(post_id)}},
        {"$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "_id",
            "as": "author"
        }},
        {"$unwind": {"path": "$author", "preserveNullAndEmptyArrays": True}},
        # include all fields including comments array for job detail screen
        {"$project": {
            "_id": 1, "type": 1, "user_id": 1,
            "company": 1, "company_logo": 1, "job_title": 1,
            "location": 1, "salary": 1, "experience": 1,
            "skills": 1, "description": 1, "likes": 1,
            "comments": 1, "comments_count": 1,
            "referrals": 1, "can_refer": 1, "created_at": 1,
            "author.name": 1, "author.avatar": 1,
            "author.title": 1, "author.company": 1, "author._id": 1,
        }}
    ]
    cursor = posts_col.aggregate(pipeline)
    results = [p async for p in cursor]
    return results[0] if results else None


async def delete_post(post_id: str):
    await posts_col.delete_one({"_id": ObjectId(post_id)})


async def toggle_like(post_id: str, user_id: ObjectId) -> bool:
    """Returns True if liked, False if unliked."""
    post = await posts_col.find_one({"_id": ObjectId(post_id)}, {"liked_by": 1})
    already_liked = user_id in post.get("liked_by", [])

    if already_liked:
        await posts_col.update_one(
            {"_id": ObjectId(post_id)},
            {"$pull": {"liked_by": user_id}, "$inc": {"likes": -1}}
        )
        return False
    else:
        await posts_col.update_one(
            {"_id": ObjectId(post_id)},
            {"$addToSet": {"liked_by": user_id}, "$inc": {"likes": 1}}
        )
        return True


async def add_comment(post_id: str, comment: dict):
    await posts_col.update_one(
        {"_id": ObjectId(post_id)},
        {
            "$push": {"comments": comment},
            "$inc": {"comments_count": 1}
        }
    )


async def get_posts_by_user(user_id: str) -> list:
    cursor = posts_col.find({"user_id": ObjectId(user_id)}).sort("created_at", -1)
    return [p async for p in cursor]


async def increment_referral_count(post_id: str):
    await posts_col.update_one(
        {"_id": ObjectId(post_id)},
        {"$inc": {"referrals": 1}}
    )
