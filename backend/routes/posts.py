from fastapi import APIRouter, HTTPException, Depends
from models.post import PostCreate, CommentCreate
from middleware.auth import get_current_user
from db.queries.post_queries import (
    create_post, get_feed, get_post_by_id,
    delete_post, toggle_like, add_comment, get_posts_by_user
)
from db.queries.notification_queries import create_notification
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/api/posts", tags=["Posts"])


def fmt_comment(c: dict) -> dict:
    c["id"] = str(c.pop("_id", ""))
    c["user_id"] = str(c.get("user_id", ""))
    return c


def fmt(post: dict) -> dict:
    post["id"] = str(post.pop("_id"))
    if "user_id" in post:
        post["user_id"] = str(post["user_id"])
    if "author" in post and post["author"]:
        post["author"]["id"] = str(post["author"].pop("_id", ""))
    # serialize liked_by list
    post["liked_by"] = [str(u) for u in post.get("liked_by", [])]
    # serialize comments
    post["comments"] = [fmt_comment(c) for c in post.get("comments", [])]
    return post
    return post


@router.get("/user/{user_id}")
async def posts_by_user(user_id: str, current_user=Depends(get_current_user)):
    """Get all posts by a specific user — used by profile screen."""
    posts = await get_posts_by_user(user_id)
    return [fmt(p) for p in posts]


@router.post("/", status_code=201)
async def create(body: PostCreate, current_user=Depends(get_current_user)):
    doc = {
        **body.model_dump(),
        "user_id": current_user["_id"],
        "likes": 0,
        "liked_by": [],
        "comments": [],
        "comments_count": 0,
        "referrals": 0,
        "created_at": datetime.utcnow(),
    }
    post_id = await create_post(doc)
    return {"id": post_id, **body.model_dump()}


@router.get("/")
async def feed(skip: int = 0, limit: int = 20, current_user=Depends(get_current_user)):
    posts = await get_feed(skip=skip, limit=limit)
    return [fmt(p) for p in posts]


@router.get("/{post_id}")
async def get_one(post_id: str, current_user=Depends(get_current_user)):
    post = await get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return fmt(post)


@router.delete("/{post_id}")
async def remove(post_id: str, current_user=Depends(get_current_user)):
    post = await get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not your post")
    await delete_post(post_id)
    return {"message": "Post deleted"}


@router.post("/{post_id}/like")
async def like(post_id: str, current_user=Depends(get_current_user)):
    post = await get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    liked = await toggle_like(post_id, current_user["_id"])

    if liked and post["user_id"] != current_user["_id"]:
        await create_notification(
            type_="like",
            from_user_id=current_user["_id"],
            to_user_id=post["user_id"],
            message=f"{current_user['name']} liked your post",
            ref_id=ObjectId(post_id),
        )
    return {"liked": liked}


@router.post("/{post_id}/comment")
async def comment(post_id: str, body: CommentCreate, current_user=Depends(get_current_user)):
    post = await get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment_doc = {
        "_id": ObjectId(),
        "user_id": current_user["_id"],
        "user_name": current_user["name"],
        "text": body.text,
        "created_at": datetime.utcnow(),
    }
    await add_comment(post_id, comment_doc)

    if post["user_id"] != current_user["_id"]:
        await create_notification(
            type_="comment",
            from_user_id=current_user["_id"],
            to_user_id=post["user_id"],
            message=f"{current_user['name']} commented on your post",
            ref_id=ObjectId(post_id),
        )
    return {"message": "Comment added"}
