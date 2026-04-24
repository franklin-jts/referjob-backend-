from fastapi import APIRouter, Depends
from models.message import MessageSend
from middleware.auth import get_current_user
from db.queries.message_queries import (
    send_message, get_conversation,
    mark_messages_read, get_user_chats
)
from bson import ObjectId

router = APIRouter(prefix="/api/messages", tags=["Messages"])


def fmt_msg(m: dict) -> dict:
    m["id"] = str(m.pop("_id", ""))
    m["sender_id"] = str(m.get("sender_id", ""))
    m["receiver_id"] = str(m.get("receiver_id", ""))
    return m


def fmt_chat(c: dict) -> dict:
    c["id"] = str(c.pop("_id", ""))
    if "other_user" in c and c["other_user"]:
        c["other_user"]["id"] = str(c["other_user"].pop("_id", ""))
    return c


@router.post("/", status_code=201)
async def send(body: MessageSend, current_user=Depends(get_current_user)):
    """Send a message to another user."""
    msg_id = await send_message(
        sender_id=current_user["_id"],
        receiver_id=ObjectId(body.receiver_id),
        text=body.text,
    )
    return {"id": msg_id}


@router.get("/chats")
async def chats(current_user=Depends(get_current_user)):
    """
    Get all chat threads for the current user.
    Used by messages.tsx to render the inbox list.
    Returns each chat with the other user's profile info.
    """
    result = await get_user_chats(current_user["_id"])
    return [fmt_chat(c) for c in result]


@router.get("/{other_user_id}")
async def conversation(other_user_id: str, current_user=Depends(get_current_user)):
    """
    Get full conversation with another user.
    Used by chat/[id].tsx — the [id] param is the other user's _id.
    Also marks all their messages to you as read.
    """
    msgs = await get_conversation(current_user["_id"], ObjectId(other_user_id))
    await mark_messages_read(current_user["_id"], ObjectId(other_user_id))
    return [fmt_msg(m) for m in msgs]
