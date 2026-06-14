from fastapi import APIRouter

from app.db.database import SessionLocal
from app.models.alert import Alert

router = APIRouter()


@router.get("/alerts")
def get_alerts():

    db = SessionLocal()

    try:
        alerts = (
            db.query(Alert)
            .order_by(
                Alert.created_at.desc()
            )
            .all()
        )

        return [
            {
                "title": alert.title,
                "event_type": alert.event_type,
                "importance_score":
                    alert.importance_score
            }
            for alert in alerts
        ]

    finally:
        db.close()
