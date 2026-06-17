from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.db.database import SessionLocal
from app.models.twitter_follow import TwitterFollow
from app.models.tweet_notification import TweetNotification

router = APIRouter(prefix="/twitter", tags=["Twitter"])


class AddFollowRequest(BaseModel):
    handle: str          # e.g. "elonmusk" (without @)
    label: Optional[str] = None  # e.g. "Elon Musk"


# ── GET /twitter/follows ──────────────────────────────────────────────────────

@router.get("/follows")
def get_follows():
    db = SessionLocal()
    try:
        follows = db.query(TwitterFollow).order_by(
            TwitterFollow.created_at.desc()
        ).all()
        return [
            {
                "id": str(f.id),
                "handle": f.handle,
                "label": f.label or f"@{f.handle}",
                "is_active": f.is_active,
            }
            for f in follows
        ]
    finally:
        db.close()


# ── POST /twitter/follows ─────────────────────────────────────────────────────

@router.post("/follows")
def add_follow(data: AddFollowRequest):
    handle = data.handle.lstrip("@").strip().lower()

    if not handle:
        raise HTTPException(status_code=400, detail="Handle cannot be empty")

    db = SessionLocal()
    try:
        existing = (
            db.query(TwitterFollow)
            .filter(TwitterFollow.handle == handle)
            .first()
        )
        if existing:
            # Reactivate if previously deleted
            if not existing.is_active:
                existing.is_active = True
                db.commit()
                return {"message": f"@{handle} reactivated"}
            raise HTTPException(
                status_code=400,
                detail=f"@{handle} is already being followed"
            )

        follow = TwitterFollow(
            handle=handle,
            label=data.label or f"@{handle}",
        )
        db.add(follow)
        db.commit()
        return {"message": f"Now following @{handle}"}

    finally:
        db.close()


# ── DELETE /twitter/follows/{id} ──────────────────────────────────────────────

@router.delete("/follows/{follow_id}")
def delete_follow(follow_id: str):
    db = SessionLocal()
    try:
        follow = (
            db.query(TwitterFollow)
            .filter(TwitterFollow.id == follow_id)
            .first()
        )
        if not follow:
            raise HTTPException(status_code=404, detail="Follow not found")

        db.delete(follow)
        db.commit()
        return {"message": f"Unfollowed @{follow.handle}"}

    finally:
        db.close()


# ── GET /twitter/notifications ────────────────────────────────────────────────

@router.get("/notifications")
def get_tweet_notifications():
    db = SessionLocal()
    try:
        notifications = (
            db.query(TweetNotification)
            .order_by(TweetNotification.created_at.desc())
            .limit(50)
            .all()
        )
        return [
            {
                "id": str(n.id),
                "handle": n.handle,
                "label": n.label,
                "tweet_text": n.tweet_text,
                "tweet_url": n.tweet_url,
                "event_type": n.event_type,
                "importance_score": n.importance_score,
                "summary": n.summary,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ]
    finally:
        db.close()


# ── PATCH /twitter/notifications/{id}/read ────────────────────────────────────

@router.patch("/notifications/{notification_id}/read")
def mark_as_read(notification_id: str):
    db = SessionLocal()
    try:
        notif = (
            db.query(TweetNotification)
            .filter(TweetNotification.id == notification_id)
            .first()
        )
        if not notif:
            raise HTTPException(status_code=404, detail="Notification not found")

        notif.is_read = True
        db.commit()
        return {"message": "Marked as read"}

    finally:
        db.close()