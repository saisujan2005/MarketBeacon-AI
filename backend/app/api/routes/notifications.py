from fastapi import APIRouter

from app.db.database import SessionLocal
from app.models.notification import Notification

router = APIRouter()


@router.get("/notifications")
def get_notifications():

    db = SessionLocal()

    try:
        notifications = (
            db.query(Notification)
            .order_by(
                Notification.created_at.desc()
            )
            .all()
        )

        return [
            {
                "keyword": n.keyword,
                "title": n.title,
                "is_read": n.is_read
            }
            for n in notifications
        ]

    finally:
        db.close()