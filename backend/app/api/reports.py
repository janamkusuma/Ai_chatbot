from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Float
from datetime import datetime, timedelta
import os, json

from app.auth import get_current_user
from app.database import get_db
from app.models import Chat, Message, QuizScore  # ✅ use SQLAlchemy model

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/summary")
def reports_summary(user=Depends(get_current_user), db: Session = Depends(get_db)):
    email = getattr(user, "email", None) or getattr(user, "username", None) or "unknown"
    role = getattr(user, "role", "USER")

    # -------------------------
    # ✅ QUIZ STATS (Postgres)
    # -------------------------
    q = db.query(QuizScore)

    if role != "ADMIN":
        q = q.filter(QuizScore.user_email == email)

    quiz_attempts = q.count()

    # average percent = avg(score/total) * 100
    avgp = (
        q.with_entities(func.avg(cast(QuizScore.score, Float) / func.nullif(QuizScore.total, 0)))
        .scalar()
    )
    avg_percent = round(((avgp or 0) * 100), 2)

    # last 10 attempts
    last10 = (
        q.order_by(QuizScore.id.desc())
        .limit(10)
        .all()
    )

    quiz_last10 = []
    for r in reversed(last10):
        total = r.total or 0
        pct = (r.score / total * 100) if total else 0
        quiz_last10.append({
            "date": r.created_at.isoformat() if r.created_at else None,
            "score": r.score,
            "total": total,
            "percent": round(pct, 2),
        })

    # -------------------------
    # ✅ CHAT STATS (SQLAlchemy)
    # -------------------------
    # Admin can see overall chat totals (optional)
    if role == "ADMIN":
        total_chats = db.query(Chat).count()
        total_msgs = db.query(Message).count()
    else:
        total_chats = db.query(Chat).filter(Chat.user_id == user.id).count()
        total_msgs = (
            db.query(Message)
            .join(Chat, Chat.id == Message.chat_id)
            .filter(Chat.user_id == user.id)
            .count()
        )

    # messages per day (last 30 days)
    since = datetime.utcnow() - timedelta(days=30)

    if role == "ADMIN":
        msgs = db.query(Message.created_at).filter(Message.created_at >= since).all()
    else:
        msgs = (
            db.query(Message.created_at)
            .join(Chat, Chat.id == Message.chat_id)
            .filter(Chat.user_id == user.id, Message.created_at >= since)
            .all()
        )

    per_day = {}
    for (dt,) in msgs:
        key = dt.date().isoformat()
        per_day[key] = per_day.get(key, 0) + 1

    # user vs assistant ratio
    if role == "ADMIN":
        user_count = db.query(Message).filter(Message.role == "user").count()
        assistant_count = db.query(Message).filter(Message.role == "assistant").count()
    else:
        user_count = (
            db.query(Message)
            .join(Chat, Chat.id == Message.chat_id)
            .filter(Chat.user_id == user.id, Message.role == "user")
            .count()
        )
        assistant_count = (
            db.query(Message)
            .join(Chat, Chat.id == Message.chat_id)
            .filter(Chat.user_id == user.id, Message.role == "assistant")
            .count()
        )

    return {
        "kpis": {
            "quiz_attempts": quiz_attempts,
            "avg_quiz_percent": avg_percent,
            "total_chats": total_chats,
            "total_messages": total_msgs
        },
        "quiz_last10": quiz_last10,
        "messages_per_day": per_day,
        "role_ratio": {"user": user_count, "assistant": assistant_count}
    }


@router.get("/ml-metrics")
def ml_metrics(user=Depends(get_current_user)):
    # backend/ml_assets/outputs/metrics.json
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # backend/app
    metrics_path = os.path.join(base_dir, "ml_assets", "outputs", "metrics.json")

    if not os.path.exists(metrics_path):
        return {"ok": False, "error": "metrics.json not found", "path": metrics_path}

    with open(metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {"ok": True, "metrics": data}