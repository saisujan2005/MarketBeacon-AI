from fastapi import APIRouter
from app.db.database import SessionLocal
from app.models.watchlist import Watchlist

import uuid

router = APIRouter()


@router.get("/watchlists")
def get_watchlists():

    db = SessionLocal()

    try:
        watchlists = db.query(Watchlist).all()

        return [
            {
                "id": str(w.id),
                "keyword": w.keyword
            }
            for w in watchlists
        ]

    finally:
        db.close()


@router.post("/watchlists")
def add_watchlist(data: dict):

    db = SessionLocal()

    try:

        watchlist = Watchlist(
            id=uuid.uuid4(),
            keyword=data["keyword"]
        )

        db.add(watchlist)
        db.commit()

        return {
            "message": "Watchlist added successfully"
        }

    finally:
        db.close()


@router.delete("/watchlists/{watchlist_id}")
def delete_watchlist(watchlist_id: str):

    db = SessionLocal()

    try:

        watchlist = (
            db.query(Watchlist)
            .filter(
                Watchlist.id == watchlist_id
            )
            .first()
        )

        if watchlist:
            db.delete(watchlist)
            db.commit()

        return {
            "message": "Watchlist deleted"
        }

    finally:
        db.close()