# backend/app/api/feedback.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone

from app.auth import get_current_user
from app.database import get_db
from app.models import Feedback

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


class FeedbackIn(BaseModel):
    rating: int
    category: str = "general"
    message: str


def migrate_feedback_table(db: Session):
    """
    One-time safe migration for Postgres:
    Adds missing columns without deleting data.
    (Works even if table already exists with old schema)
    """
    db.execute(text("ALTER TABLE feedback ADD COLUMN IF NOT EXISTS user_email VARCHAR"))
    db.execute(text("ALTER TABLE feedback ADD COLUMN IF NOT EXISTS rating INTEGER"))
    db.execute(text("ALTER TABLE feedback ADD COLUMN IF NOT EXISTS category VARCHAR"))
    db.execute(text("ALTER TABLE feedback ADD COLUMN IF NOT EXISTS message TEXT"))
    db.execute(text("ALTER TABLE feedback ADD COLUMN IF NOT EXISTS created_at TIMESTAMP"))
    db.commit()


@router.post("/submit")
def submit_feedback(
    body: FeedbackIn,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    # ✅ ensure table has needed columns
    migrate_feedback_table(db)

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
    db.refresh(row)

    return {"ok": True, "message": "submitted", "id": row.id}


@router.get("/my")
def my_feedback(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    # ✅ ensure table has needed columns
    migrate_feedback_table(db)

    email = getattr(user, "email", None) or getattr(user, "username", "unknown")
    role = getattr(user, "role", "USER")

    q = db.query(Feedback)

    if role != "ADMIN":
        q = q.filter(Feedback.user_email == email)

    rows = q.order_by(Feedback.id.desc()).limit(500).all()

    out = []
    for r in rows:
        out.append(
            {
                "id": r.id,
                "user_email": getattr(r, "user_email", None),
                "rating": getattr(r, "rating", None),
                "category": getattr(r, "category", None),
                "message": getattr(r, "message", None),
                "created_at": r.created_at.isoformat() if getattr(r, "created_at", None) else None,
            }
        )

    return out