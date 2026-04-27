from fastapi import APIRouter, HTTPException, Depends
from models.story import StoryCreate
from middleware.auth import get_current_user
from db.queries.story_queries import (
    create_story, get_stories, get_story_by_id, delete_story
)
from datetime import datetime

router = APIRouter(prefix="/api/stories", tags=["Stories"])


def fmt(story: dict) -> dict:
    story["id"] = str(story.pop("_id"))
    if "user_id" in story:
        story["user_id"] = str(story["user_id"])
    return story


@router.post("/", status_code=201)
async def create(body: StoryCreate, current_user=Depends(get_current_user)):
    doc = {
        **body.model_dump(),
        "user_id": current_user["_id"],
        "created_at": datetime.utcnow(),
    }
    story_id = await create_story(doc)
    return {"id": story_id, **body.model_dump()}


@router.get("/")
async def list_stories(current_user=Depends(get_current_user)):
    stories = await get_stories()
    return [fmt(s) for s in stories]


@router.delete("/{story_id}")
async def remove(story_id: str, current_user=Depends(get_current_user)):
    story = await get_story_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if str(story["user_id"]) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not your story")
    await delete_story(story_id)
    return {"message": "Story deleted"}
