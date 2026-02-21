# backend/app/api/quiz.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.auth import get_current_user
from app.database import get_db
from app.models import QuizScore

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])


class QuizSaveIn(BaseModel):
    score: int
    total: int


@router.post("/save")
def save_quiz_score(
    body: QuizSaveIn,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    # validate
    if body.total <= 0:
        raise HTTPException(status_code=400, detail="Total must be > 0")
    if body.score < 0 or body.score > body.total:
        raise HTTPException(status_code=400, detail="Invalid score")

    # user object safe
    if isinstance(user, dict):
        email = user.get("email") or user.get("username") or "unknown"
    else:
        email = getattr(user, "email", None) or getattr(user, "username", None) or "unknown"

    row = QuizScore(
        user_email=email,
        score=int(body.score),
        total=int(body.total),
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()

    return {"message": "saved"}


@router.get("/my-scores")
def my_scores(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Get email safely
    email = getattr(user, "email", None) or getattr(user, "username", "unknown")
    role = getattr(user, "role", "USER")

    q = db.query(QuizScore)

    # ADMIN → all quiz history
    if role != "ADMIN":
        q = q.filter(QuizScore.user_email == email)

    rows = q.order_by(QuizScore.id.desc()).limit(500).all()

    # response format match your frontend
    if role == "ADMIN":
        return [
            {
                "user_email": r.user_email,
                "score": r.score,
                "total": r.total,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    return [
        {
            "score": r.score,
            "total": r.total,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]