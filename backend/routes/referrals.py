from fastapi import APIRouter, HTTPException, Depends
from models.referral import ReferralRequest
from middleware.auth import get_current_user
from db.queries.referral_queries import (
    create_referral, find_pending_referral, get_referral_by_id,
    get_my_requests, get_my_referrals, update_referral_status
)
from db.queries.post_queries import get_post_by_id, increment_referral_count
from db.queries.user_queries import find_user_by_id, increment_referral_given, increment_referral_received
from db.queries.notification_queries import create_notification
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/api/referrals", tags=["Referrals"])


def fmt(r: dict) -> dict:
    r["id"] = str(r.pop("_id"))
    for key in ("requester_id", "referrer_id", "post_id", "ref_id"):
        if key in r and r[key]:
            r[key] = str(r[key])
    if "post" in r and r["post"]:
        r["post"]["id"] = str(r["post"].pop("_id", ""))
    if "referrer" in r and r["referrer"]:
        r["referrer"]["id"] = str(r["referrer"].pop("_id", ""))
    if "requester" in r and r["requester"]:
        r["requester"]["id"] = str(r["requester"].pop("_id", ""))
    return r


@router.post("/", status_code=201)
async def request_referral(body: ReferralRequest, current_user=Depends(get_current_user)):
    post = await get_post_by_id(body.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    referrer = await find_user_by_id(body.referrer_id)
    if not referrer:
        raise HTTPException(status_code=404, detail="Referrer not found")

    existing = await find_pending_referral(
        current_user["_id"], body.referrer_id, body.post_id
    )
    if existing:
        raise HTTPException(status_code=400, detail="Referral request already pending")

    doc = {
        "requester_id": current_user["_id"],
        "referrer_id": ObjectId(body.referrer_id),
        "post_id": ObjectId(body.post_id),
        "resume_url": body.resume_url,
        "note": body.note,
        "friend_name": body.friend_name,
        "friend_email": body.friend_email,
        "app_username": body.app_username,
        "mobile_number": body.mobile_number,
        "status": "pending",
        "created_at": datetime.utcnow(),
    }
    referral_id = await create_referral(doc)

    await create_notification(
        type_="referral_request",
        from_user_id=current_user["_id"],
        to_user_id=ObjectId(body.referrer_id),
        message=f"{current_user['name']} requested a referral for {post['job_title']}",
        ref_id=ObjectId(referral_id),
    )
    return {"id": referral_id, "status": "pending"}


@router.get("/my-requests")
async def my_requests(current_user=Depends(get_current_user)):
    results = await get_my_requests(current_user["_id"])
    return [fmt(r) for r in results]


@router.get("/my-referrals")
async def my_referrals(current_user=Depends(get_current_user)):
    results = await get_my_referrals(current_user["_id"])
    return [fmt(r) for r in results]


@router.put("/{referral_id}/status")
async def update_status(referral_id: str, status: str, current_user=Depends(get_current_user)):
    if status not in ["accepted", "rejected", "submitted"]:
        raise HTTPException(status_code=400, detail="Invalid status. Use: accepted | rejected | submitted")

    referral = await get_referral_by_id(referral_id)
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    if referral["referrer_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    await update_referral_status(referral_id, status)

    if status == "accepted":
        await increment_referral_given(str(current_user["_id"]))
        await increment_referral_received(str(referral["requester_id"]))
        await increment_referral_count(str(referral["post_id"]))

    await create_notification(
        type_=f"referral_{status}",
        from_user_id=current_user["_id"],
        to_user_id=referral["requester_id"],
        message=f"{current_user['name']} {status} your referral request",
        ref_id=ObjectId(referral_id),
    )
    return {"message": f"Referral {status}"}
