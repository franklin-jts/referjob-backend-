"""
MongoDB queries for the stories collection (used by web admin).
"""
import database
from bson import ObjectId
from datetime import datetime


async def create_story(data: dict) -> str:
    result = await database.stories_col.insert_one(data)
    return str(result.inserted_id)


async def get_stories() -> list:
    cursor = database.stories_col.find().sort("created_at", -1)
    return [s async for s in cursor]


async def get_story_by_id(story_id: str):
    return await database.stories_col.find_one({"_id": ObjectId(story_id)})


async def delete_story(story_id: str):
    await database.stories_col.delete_one({"_id": ObjectId(story_id)})
