# MongoDB Queries — Job Referral App
> All queries used in this project, collection by collection.
> Database: `jobreferalapp` | Driver: `motor` (async) | ODM: raw PyMongo queries

---

## Database Connection (`database.py`)

```python
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017/jobreferalapp"
client    = AsyncIOMotorClient(MONGO_URI)
db        = client.jobreferalapp
```

### Collections
| Variable | Collection Name | Purpose |
|---|---|---|
| `users_col` | `users` | User profiles, auth, connections |
| `posts_col` | `posts` | Job posts & referral offers |
| `messages_col` | `messages` | Individual chat messages |
| `chats_col` | `chats` | Chat thread summaries (inbox) |
| `referrals_col` | `referrals` | Referral requests & status |
| `notifications_col` | `notifications` | In-app notifications |

---

## USERS Collection

### Document Shape
```json
{
  "_id": ObjectId,
  "name": "string",
  "email": "string",
  "password": "bcrypt_hash",
  "title": "string",
  "company": "string",
  "location": "string",
  "bio": "string",
  "skills": ["string"],
  "avatar": "url_string",
  "connections": 0,
  "referral_given": 0,
  "referral_received": 0,
  "connection_ids": [ObjectId],
  "created_at": ISODate
}
```

### 1. Insert a new user
```python
result = await users_col.insert_one(data)
# returns inserted_id
```

### 2. Find user by email (login / duplicate check)
```python
await users_col.find_one({"email": email})
```

### 3. Find user by ID
```python
await users_col.find_one({"_id": ObjectId(user_id)})
```

### 4. Update user profile fields
```python
await users_col.update_one(
    {"_id": ObjectId(user_id)},
    {"$set": {"title": "...", "bio": "...", "skills": [...]}}
)
```

### 5. Search users by name (case-insensitive regex)
```python
await users_col.find(
    {"name": {"$regex": "search_term", "$options": "i"}}
).limit(20)
```

### 6. Add connection (both sides, no duplicates)
```python
# Add target to my connections
await users_col.update_one(
    {"_id": ObjectId(user_id)},
    {
        "$addToSet": {"connection_ids": ObjectId(target_id)},
        "$inc": {"connections": 1}
    }
)
# Add me to target's connections
await users_col.update_one(
    {"_id": ObjectId(target_id)},
    {
        "$addToSet": {"connection_ids": ObjectId(user_id)},
        "$inc": {"connections": 1}
    }
)
```
> `$addToSet` prevents duplicate connections automatically.

### 7. Increment referral counters
```python
# When referral is accepted — update referrer
await users_col.update_one(
    {"_id": ObjectId(user_id)},
    {"$inc": {"referral_given": 1}}
)
# Update the person who received the referral
await users_col.update_one(
    {"_id": ObjectId(user_id)},
    {"$inc": {"referral_received": 1}}
)
```

---

## POSTS Collection

### Document Shape
```json
{
  "_id": ObjectId,
  "type": "job_post | referral_offer",
  "user_id": ObjectId,
  "company": "string",
  "company_logo": "url",
  "job_title": "string",
  "location": "string",
  "salary": "string",
  "experience": "string",
  "skills": ["string"],
  "description": "string",
  "likes": 0,
  "liked_by": [ObjectId],
  "comments": [
    {
      "_id": ObjectId,
      "user_id": ObjectId,
      "user_name": "string",
      "text": "string",
      "created_at": ISODate
    }
  ],
  "comments_count": 0,
  "referrals": 0,
  "can_refer": true,
  "created_at": ISODate
}
```

### 1. Insert a new post
```python
result = await posts_col.insert_one(data)
```

### 2. Get feed — newest first, with author info joined ($lookup)
```python
pipeline = [
    {"$sort": {"created_at": -1}},
    {"$skip": skip},
    {"$limit": limit},
    {"$lookup": {
        "from": "users",
        "localField": "user_id",
        "foreignField": "_id",
        "as": "author"
    }},
    {"$unwind": {"path": "$author", "preserveNullAndEmptyArrays": True}},
    {"$project": {
        "_id": 1, "type": 1, "company": 1, "company_logo": 1,
        "job_title": 1, "location": 1, "salary": 1, "experience": 1,
        "skills": 1, "description": 1, "likes": 1, "referrals": 1,
        "can_refer": 1, "created_at": 1, "comments_count": 1,
        "author.name": 1, "author.avatar": 1,
        "author.title": 1, "author.company": 1,
    }}
]
cursor = posts_col.aggregate(pipeline)
```

### 3. Get single post by ID (with full comments + author)
```python
pipeline = [
    {"$match": {"_id": ObjectId(post_id)}},
    {"$lookup": {
        "from": "users",
        "localField": "user_id",
        "foreignField": "_id",
        "as": "author"
    }},
    {"$unwind": {"path": "$author", "preserveNullAndEmptyArrays": True}},
    {"$project": {
        "_id": 1, "type": 1, "user_id": 1,
        "company": 1, "company_logo": 1, "job_title": 1,
        "location": 1, "salary": 1, "experience": 1,
        "skills": 1, "description": 1, "likes": 1,
        "comments": 1, "comments_count": 1,
        "referrals": 1, "can_refer": 1, "created_at": 1,
        "author.name": 1, "author.avatar": 1,
        "author.title": 1, "author.company": 1, "author._id": 1,
    }}
]
```

### 4. Delete a post
```python
await posts_col.delete_one({"_id": ObjectId(post_id)})
```

### 5. Toggle like (atomic — no race conditions)
```python
# Check if already liked
post = await posts_col.find_one({"_id": ObjectId(post_id)}, {"liked_by": 1})
already_liked = user_id in post.get("liked_by", [])

if already_liked:
    # Unlike
    await posts_col.update_one(
        {"_id": ObjectId(post_id)},
        {"$pull": {"liked_by": user_id}, "$inc": {"likes": -1}}
    )
else:
    # Like — $addToSet prevents double-likes
    await posts_col.update_one(
        {"_id": ObjectId(post_id)},
        {"$addToSet": {"liked_by": user_id}, "$inc": {"likes": 1}}
    )
```

### 6. Add a comment
```python
await posts_col.update_one(
    {"_id": ObjectId(post_id)},
    {
        "$push": {"comments": {
            "_id": ObjectId(),
            "user_id": user_id,
            "user_name": "string",
            "text": "comment text",
            "created_at": datetime.utcnow()
        }},
        "$inc": {"comments_count": 1}
    }
)
```

### 7. Get all posts by a user (profile screen)
```python
await posts_col.find(
    {"user_id": ObjectId(user_id)}
).sort("created_at", -1)
```

### 8. Increment referral count on a post
```python
await posts_col.update_one(
    {"_id": ObjectId(post_id)},
    {"$inc": {"referrals": 1}}
)
```

---

## REFERRALS Collection

### Document Shape
```json
{
  "_id": ObjectId,
  "requester_id": ObjectId,
  "referrer_id": ObjectId,
  "post_id": ObjectId,
  "status": "pending | accepted | rejected | submitted",
  "resume_url": "string",
  "note": "string",
  "friend_name": "string",
  "friend_email": "string",
  "app_username": "string",
  "mobile_number": "string",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### 1. Insert a referral request
```python
result = await referrals_col.insert_one(data)
```

### 2. Check for duplicate pending request
```python
await referrals_col.find_one({
    "requester_id": requester_id,
    "referrer_id": ObjectId(referrer_id),
    "post_id": ObjectId(post_id),
    "status": "pending"
})
```

### 3. Find referral by ID
```python
await referrals_col.find_one({"_id": ObjectId(referral_id)})
```

### 4. Get my sent requests — joined with post + referrer info
```python
pipeline = [
    {"$match": {"requester_id": requester_id}},
    {"$sort": {"created_at": -1}},
    {"$lookup": {
        "from": "posts",
        "localField": "post_id",
        "foreignField": "_id",
        "as": "post"
    }},
    {"$unwind": {"path": "$post", "preserveNullAndEmptyArrays": True}},
    {"$lookup": {
        "from": "users",
        "localField": "referrer_id",
        "foreignField": "_id",
        "as": "referrer"
    }},
    {"$unwind": {"path": "$referrer", "preserveNullAndEmptyArrays": True}},
    {"$project": {
        "_id": 1, "status": 1, "resume_url": 1, "note": 1, "created_at": 1,
        "post.job_title": 1, "post.company": 1,
        "referrer.name": 1, "referrer.avatar": 1, "referrer.company": 1,
    }}
]
```

### 5. Get referrals I need to action — joined with post + requester info
```python
pipeline = [
    {"$match": {"referrer_id": referrer_id}},
    {"$sort": {"created_at": -1}},
    {"$lookup": {
        "from": "posts",
        "localField": "post_id",
        "foreignField": "_id",
        "as": "post"
    }},
    {"$unwind": {"path": "$post", "preserveNullAndEmptyArrays": True}},
    {"$lookup": {
        "from": "users",
        "localField": "requester_id",
        "foreignField": "_id",
        "as": "requester"
    }},
    {"$unwind": {"path": "$requester", "preserveNullAndEmptyArrays": True}},
    {"$project": {
        "_id": 1, "status": 1, "resume_url": 1, "note": 1, "created_at": 1,
        "post.job_title": 1, "post.company": 1,
        "requester.name": 1, "requester.avatar": 1, "requester.title": 1,
    }}
]
```

### 6. Update referral status
```python
await referrals_col.update_one(
    {"_id": ObjectId(referral_id)},
    {"$set": {"status": "accepted", "updated_at": datetime.utcnow()}}
)
# status options: "pending" | "accepted" | "rejected" | "submitted"
```

---

## MESSAGES + CHATS Collections

### Message Document Shape
```json
{
  "_id": ObjectId,
  "chat_id": "userId1_userId2",
  "sender_id": ObjectId,
  "receiver_id": ObjectId,
  "text": "string",
  "read": false,
  "created_at": ISODate
}
```

### Chat Document Shape
```json
{
  "_id": ObjectId,
  "chat_id": "userId1_userId2",
  "participants": [ObjectId, ObjectId],
  "last_message": "string",
  "unread_count": 0,
  "updated_at": ISODate
}
```

> `chat_id` is deterministic: both user IDs sorted alphabetically and joined with `_`.
> This means the same chat thread is always found regardless of who queries it.

### 1. Send a message + upsert chat summary
```python
# Build deterministic chat_id
ids = sorted([str(sender_id), str(receiver_id)])
chat_id = f"{ids[0]}_{ids[1]}"

# Insert message
await messages_col.insert_one({
    "chat_id": chat_id,
    "sender_id": sender_id,
    "receiver_id": receiver_id,
    "text": text,
    "read": False,
    "created_at": datetime.utcnow(),
})

# Upsert chat summary (creates if not exists)
await chats_col.update_one(
    {"chat_id": chat_id},
    {
        "$set": {
            "participants": [sender_id, receiver_id],
            "last_message": text,
            "updated_at": datetime.utcnow(),
        },
        "$inc": {"unread_count": 1}
    },
    upsert=True
)
```

### 2. Get full conversation between two users (oldest first)
```python
await messages_col.find(
    {"chat_id": chat_id}
).sort("created_at", 1)
```

### 3. Mark all messages as read
```python
# Mark messages as read
await messages_col.update_many(
    {"chat_id": chat_id, "receiver_id": user_a, "read": False},
    {"$set": {"read": True}}
)
# Reset unread counter on chat
await chats_col.update_one(
    {"chat_id": chat_id},
    {"$set": {"unread_count": 0}}
)
```

### 4. Get all chat threads for a user (inbox) — with other user's profile
```python
pipeline = [
    {"$match": {"participants": user_id}},
    {"$sort": {"updated_at": -1}},
    # Compute the other participant's ID
    {"$addFields": {
        "other_user_id": {
            "$arrayElemAt": [
                {"$filter": {
                    "input": "$participants",
                    "as": "p",
                    "cond": {"$ne": ["$$p", user_id]}
                }},
                0
            ]
        }
    }},
    # Join their profile
    {"$lookup": {
        "from": "users",
        "localField": "other_user_id",
        "foreignField": "_id",
        "as": "other_user"
    }},
    {"$unwind": {"path": "$other_user", "preserveNullAndEmptyArrays": True}},
    {"$project": {
        "chat_id": 1, "last_message": 1, "unread_count": 1, "updated_at": 1,
        "other_user._id": 1, "other_user.name": 1,
        "other_user.avatar": 1, "other_user.title": 1, "other_user.company": 1,
    }}
]
```

---

## NOTIFICATIONS Collection

### Document Shape
```json
{
  "_id": ObjectId,
  "type": "like | comment | connection | referral_request | referral_accepted | referral_rejected | referral_submitted",
  "from_user_id": ObjectId,
  "to_user_id": ObjectId,
  "message": "string",
  "ref_id": ObjectId,
  "read": false,
  "created_at": ISODate
}
```

### 1. Create a notification
```python
await notifications_col.insert_one({
    "type": "like",
    "from_user_id": from_user_id,
    "to_user_id": to_user_id,
    "message": "Arjun liked your post",
    "ref_id": post_object_id,
    "read": False,
    "created_at": datetime.utcnow(),
})
```

### 2. Get notifications for a user — with sender's profile joined
```python
pipeline = [
    {"$match": {"to_user_id": user_id}},
    {"$sort": {"created_at": -1}},
    {"$limit": 50},
    {"$lookup": {
        "from": "users",
        "localField": "from_user_id",
        "foreignField": "_id",
        "as": "from_user"
    }},
    {"$unwind": {"path": "$from_user", "preserveNullAndEmptyArrays": True}},
    {"$project": {
        "_id": 1, "type": 1, "message": 1, "ref_id": 1,
        "read": 1, "created_at": 1,
        "from_user._id": 1, "from_user.name": 1, "from_user.avatar": 1,
    }}
]
```

### 3. Mark one notification as read
```python
await notifications_col.update_one(
    {"_id": ObjectId(notif_id), "to_user_id": user_id},
    {"$set": {"read": True}}
)
```

### 4. Mark ALL notifications as read
```python
await notifications_col.update_many(
    {"to_user_id": user_id, "read": False},
    {"$set": {"read": True}}
)
```

### 5. Get unread notification count (badge)
```python
await notifications_col.count_documents(
    {"to_user_id": user_id, "read": False}
)
```

---

## MongoDB Operators Used — Quick Reference

| Operator | Used For |
|---|---|
| `$set` | Update specific fields |
| `$inc` | Increment/decrement a number field |
| `$push` | Append to an array (comments) |
| `$pull` | Remove from an array (unlike) |
| `$addToSet` | Add to array only if not already present (connections, likes) |
| `$match` | Filter documents in aggregation pipeline |
| `$sort` | Sort documents |
| `$skip` / `$limit` | Pagination |
| `$lookup` | Join another collection (like SQL JOIN) |
| `$unwind` | Flatten a joined array into a single object |
| `$project` | Select which fields to return |
| `$addFields` | Compute new fields in pipeline |
| `$filter` | Filter elements inside an array field |
| `$arrayElemAt` | Get element at index from array |
| `$ne` | Not equal comparison |
| `$regex` | Pattern matching for search |
| `upsert=True` | Insert if not found, update if found |
| `count_documents` | Count matching documents |
| `update_many` | Update all matching documents |

---

## Indexes to Create (run once on startup)

Run these in MongoDB shell or add to a `create_indexes.py` script:

```js
// Users
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "name": "text" })

// Posts
db.posts.createIndex({ "created_at": -1 })
db.posts.createIndex({ "user_id": 1 })

// Messages
db.messages.createIndex({ "chat_id": 1, "created_at": 1 })
db.messages.createIndex({ "receiver_id": 1, "read": 1 })

// Chats
db.chats.createIndex({ "participants": 1 })
db.chats.createIndex({ "chat_id": 1 }, { unique: true })

// Referrals
db.referrals.createIndex({ "requester_id": 1 })
db.referrals.createIndex({ "referrer_id": 1 })
db.referrals.createIndex({ "status": 1 })

// Notifications
db.notifications.createIndex({ "to_user_id": 1, "read": 1 })
db.notifications.createIndex({ "created_at": -1 })
```
