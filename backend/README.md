# Job Referral App — FastAPI Backend

## Stack
- Python + FastAPI
- MongoDB via Motor (async driver)
- JWT authentication
- Bcrypt password hashing

## Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env      # set MONGO_URI and JWT_SECRET
uvicorn main:app --reload --port 8000
```

Swagger UI → http://localhost:8000/docs

---

## API ↔ Frontend Screen Mapping

| Screen | Method | Endpoint |
|--------|--------|----------|
| onboarding.tsx | POST | `/api/auth/register` |
| login.tsx | POST | `/api/auth/login` |
| App startup (restore session) | GET | `/api/auth/me` |
| index.tsx (feed) | GET | `/api/posts/?skip=0&limit=20` |
| index.tsx (like button) | POST | `/api/posts/{id}/like` |
| index.tsx (comment) | POST | `/api/posts/{id}/comment` |
| ReferModal.tsx | POST | `/api/referrals/` |
| job/[id].tsx (detail) | GET | `/api/posts/{id}` |
| job/[id].tsx (request referral) | POST | `/api/referrals/` |
| profile.tsx (my info) | GET | `/api/users/me` |
| profile.tsx (my posts) | GET | `/api/posts/user/{user_id}` |
| profile.tsx (edit) | PUT | `/api/users/me` |
| profile.tsx (connect) | POST | `/api/users/{id}/connect` |
| messages.tsx (inbox) | GET | `/api/messages/chats` |
| chat/[id].tsx (conversation) | GET | `/api/messages/{other_user_id}` |
| chat/[id].tsx (send) | POST | `/api/messages/` |
| notifications tab (badge) | GET | `/api/notifications/unread-count` |
| notifications tab (list) | GET | `/api/notifications/` |
| notifications tab (mark read) | PUT | `/api/notifications/{id}/read` |
| notifications tab (clear all) | PUT | `/api/notifications/read-all` |
| referrals (my requests) | GET | `/api/referrals/my-requests` |
| referrals (my referrals) | GET | `/api/referrals/my-referrals` |
| referrals (accept/reject) | PUT | `/api/referrals/{id}/status` |
| search users | GET | `/api/users/search?q=name` |
| view any profile | GET | `/api/users/{id}` |

## Auth Header
All endpoints except `/api/auth/*` require:
```
Authorization: Bearer <jwt_token>
```

## ReferModal fields accepted by POST /api/referrals/
```json
{
  "referrer_id": "user_id_of_referrer",
  "post_id": "post_id",
  "friend_name": "optional",
  "friend_email": "optional",
  "app_username": "optional",
  "mobile_number": "optional",
  "resume_url": "optional",
  "note": "optional"
}
```
