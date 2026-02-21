# backend/app/api/feedback.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.auth import get_current_user
from app.database import get_db
from app.models import Feedback

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


class FeedbackIn(BaseModel):
    rating: int
    category: str = "general"
    message: str


@router.post("/submit")
def submit_feedback(
    body: FeedbackIn,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if body.rating < 1 or body.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1 to 5")

    msg = (body.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Message is empty")

    email = getattr(user, "email", None) or getattr(user, "username", None) or "unknown"

    row = Feedback(
        user_email=email,
        rating=int(body.rating),
        category=(body.category or "general"),
        message=msg,
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()

    return {"ok": True, "message": "submitted"}


@router.get("/my")
def my_feedback(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    email = getattr(user, "email", None) or getattr(user, "username", "unknown")
    role = getattr(user, "role", "USER")

    q = db.query(Feedback)

    if role != "ADMIN":
        q = q.filter(Feedback.user_email == email)

    rows = q.order_by(Feedback.id.desc()).limit(500).all()

    return [
        {
            "id": r.id,
            "user_email": r.user_email,
            "rating": r.rating,
            "category": r.category,
            "message": r.message,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]