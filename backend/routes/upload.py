import os
import uuid
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from middleware.auth import get_current_user

router = APIRouter(prefix="/api/upload", tags=["Upload"])

BASE_URL = os.getenv("BASE_URL", "http://localhost:8002")

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/jpg"}
MAX_SIZE      = 2 * 1024 * 1024  # 2MB


@router.post("/image")
async def upload_image(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PNG and JPEG images are allowed")

    contents = await file.read()

    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 2MB limit")

    ext      = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join("uploads", filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    return {"url": f"{BASE_URL}/uploads/{filename}"}
