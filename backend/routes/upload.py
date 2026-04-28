import os
import uuid
import io
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from middleware.auth import get_current_user
from db.queries.user_queries import update_user

router = APIRouter(prefix="/api/upload", tags=["Upload"])

BASE_URL = os.getenv("BASE_URL", "http://localhost:8002")

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg"}
MAX_IMAGE_SIZE = 2 * 1024 * 1024   # 2MB
MAX_CV_SIZE    = 10 * 1024 * 1024  # 10MB


# ── Image upload ──────────────────────────────────────────────────────────────
@router.post("/image")
async def upload_image(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only PNG and JPEG images are allowed")
    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 2MB limit")
    ext      = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    with open(os.path.join("uploads", filename), "wb") as f:
        f.write(contents)
    return {"url": f"{BASE_URL}/uploads/{filename}"}


# ── ATS analysis ──────────────────────────────────────────────────────────────
def analyze_cv(content: bytes, filename: str):
    text = ""
    try:
        if filename.lower().endswith(".pdf"):
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = " ".join(p.extract_text() or "" for p in pdf.pages)
        elif filename.lower().endswith(".docx"):
            import docx
            doc = docx.Document(io.BytesIO(content))
            text = " ".join(p.text for p in doc.paragraphs)
    except Exception:
        return 40, ["Could not parse CV. Please upload a valid PDF or DOCX."]

    text_lower = text.lower()
    score = 0
    suggestions = []

    checks = [
        (any(w in text_lower for w in ["email", "@", "phone", "mobile"]),           10, "Add contact information (email, phone)"),
        (any(w in text_lower for w in ["skills", "technologies", "tools"]),          15, "Add a dedicated Skills section"),
        (any(w in text_lower for w in ["experience", "worked", "employed"]),         15, "Add Work Experience section"),
        (any(w in text_lower for w in ["education", "university", "college", "degree", "b.tech", "mba"]), 15, "Add Education section"),
        (any(w in text_lower for w in ["summary", "objective", "profile", "about"]), 10, "Add a professional Summary or Objective"),
        (any(w in text_lower for w in ["achieved", "improved", "led", "built", "developed", "managed", "increased"]), 15, "Use strong action verbs (Led, Built, Achieved)"),
        (any(c.isdigit() for c in text),                                             10, "Add quantified achievements (e.g. 'Increased sales by 30%')"),
        (len(text.split()) >= 300,                                                   10, "CV seems too short. Add more detail (aim for 400+ words)"),
    ]

    for passed, points, suggestion in checks:
        if passed:
            score += points
        else:
            suggestions.append(suggestion)

    if not suggestions:
        suggestions = ["Great CV! Consider tailoring it for each job application."]

    return min(score, 100), suggestions


# ── CV upload ─────────────────────────────────────────────────────────────────
@router.post("/cv")
async def upload_cv(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    fname = file.filename.lower()
    if not (fname.endswith(".pdf") or fname.endswith(".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")

    content = await file.read()
    if len(content) > MAX_CV_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    filename = f"cv_{current_user['_id']}_{file.filename}"
    with open(os.path.join("uploads", filename), "wb") as f:
        f.write(content)

    url = f"{BASE_URL}/uploads/{filename}"
    score, suggestions = analyze_cv(content, file.filename)

    await update_user(str(current_user["_id"]), {
        "cv_url":          url,
        "cv_filename":     file.filename,
        "ats_score":       score,
        "ats_suggestions": suggestions,
    })

    return {
        "url":             url,
        "filename":        file.filename,
        "ats_score":       score,
        "ats_suggestions": suggestions,
    }
