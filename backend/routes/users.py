from fastapi import APIRouter, HTTPException, Depends
from models.user import UserUpdate
from middleware.auth import get_current_user
from db.queries.user_queries import (
    find_user_by_id, update_user, search_users,
    add_connection, is_connected
)
from db.queries.notification_queries import create_notification

router = APIRouter(prefix="/api/users", tags=["Users"])


def fmt(user: dict) -> dict:
    user["id"] = str(user.pop("_id"))
    user.pop("password", None)
    user["connection_ids"] = [str(c) for c in user.get("connection_ids", [])]
    return user


@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    return fmt(current_user)


@router.put("/me")
async def update_me(body: UserUpdate, current_user=Depends(get_current_user)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updated = await update_user(str(current_user["_id"]), updates)
    return fmt(updated)


@router.get("/search")
async def search(q: str = "", current_user=Depends(get_current_user)):
    users = await search_users(q)
    return [fmt(u) for u in users]


@router.get("/{user_id}")
async def get_user(user_id: str, current_user=Depends(get_current_user)):
    user = await find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return fmt(user)


@router.post("/{user_id}/connect")
async def connect(user_id: str, current_user=Depends(get_current_user)):
    target = await find_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if await is_connected(str(current_user["_id"]), user_id):
        raise HTTPException(status_code=400, detail="Already connected")

    await add_connection(str(current_user["_id"]), user_id)
    await create_notification(
        type_="connection",
        from_user_id=current_user["_id"],
        to_user_id=target["_id"],
        message=f"{current_user['name']} connected with you",
    )
    return {"message": "Connected successfully"}
