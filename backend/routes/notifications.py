from fastapi import APIRouter, Depends
from middleware.auth import get_current_user
from db.queries.notification_queries import (
    get_notifications_for_user, mark_notification_read,
    mark_all_read, get_unread_count
)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


def fmt(n: dict) -> dict:
    n["id"] = str(n.pop("_id"))
    n["from_user_id"] = str(n["from_user_id"])
    n["to_user_id"] = str(n["to_user_id"])
    if n.get("ref_id"):
        n["ref_id"] = str(n["ref_id"])
    if "from_user" in n and n["from_user"]:
        n["from_user"]["id"] = str(n["from_user"].pop("_id", ""))
    return n


@router.get("/")
async def get_all(current_user=Depends(get_current_user)):
    notifs = await get_notifications_for_user(current_user["_id"])
    return [fmt(n) for n in notifs]


@router.get("/unread-count")
async def unread_count(current_user=Depends(get_current_user)):
    count = await get_unread_count(current_user["_id"])
    return {"unread": count}


@router.put("/read-all")
async def read_all(current_user=Depends(get_current_user)):
    await mark_all_read(current_user["_id"])
    return {"message": "All notifications marked as read"}


@router.put("/{notif_id}/read")
async def read_one(notif_id: str, current_user=Depends(get_current_user)):
    await mark_notification_read(notif_id, current_user["_id"])
    return {"message": "Marked as read"}
