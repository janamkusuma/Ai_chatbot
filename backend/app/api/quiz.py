# backend/app/api/quiz.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.auth import get_current_user
from app.database import get_db
from app.models import QuizScore

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])


class QuizSaveIn(BaseModel):
    score: int
    total: int


def to_utc_z(dt: datetime | None) -> str | None:
    if not dt:
        return None
    # ✅ make sure timezone-aware UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    # ✅ return "Z" format
    return dt.isoformat().replace("+00:00", "Z")


@router.post("/save")
def save_quiz_score(
    body: QuizSaveIn,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if body.total <= 0:
        raise HTTPException(status_code=400, detail="Total must be > 0")
    if body.score < 0 or body.score > body.total:
        raise HTTPException(status_code=400, detail="Invalid score")

    if isinstance(user, dict):
        email = user.get("email") or user.get("username") or "unknown"
    else:
        email = getattr(user, "email", None) or getattr(user, "username", None) or "unknown"

    row = QuizScore(
        user_email=email,
        score=int(body.score),
        total=int(body.total),
        created_at=datetime.now(timezone.utc),  # ✅ always store UTC aware
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return {"message": "saved", "created_at": to_utc_z(row.created_at)}


@router.get("/my-scores")
def my_scores(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    email = getattr(user, "email", None) or getattr(user, "username", "unknown")
    role = getattr(user, "role", "USER")

    q = db.query(QuizScore)
    if role != "ADMIN":
        q = q.filter(QuizScore.user_email == email)

    rows = q.order_by(QuizScore.id.desc()).limit(500).all()

    if role == "ADMIN":
        return [
            {
                "user_email": r.user_email,
                "score": r.score,
                "total": r.total,
                "created_at": to_utc_z(r.created_at),
            }
            for r in rows
        ]

    return [
        {
            "score": r.score,
            "total": r.total,
            "created_at": to_utc_z(r.created_at),
        }
        for r in rows
    ]