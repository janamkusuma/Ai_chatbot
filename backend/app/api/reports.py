from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import sqlite3, os

from app.auth import get_current_user
from app.database import get_db
from app.models import Chat, Message

router = APIRouter(prefix="/api/reports", tags=["Reports"])

# --- quiz sqlite (same as quiz.py) ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # backend/app
DB_PATH = os.path.join(BASE_DIR, "health.db")

def quiz_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/summary")
def reports_summary(user=Depends(get_current_user), db: Session = Depends(get_db)):
    email = getattr(user, "email", None) or getattr(user, "username", None) or "unknown"
    role = getattr(user, "role", "USER")

    conn = quiz_conn()
    cur = conn.cursor()

    # ✅ ADMIN -> all users
    if role == "ADMIN":
        cur.execute("SELECT COUNT(*) as c FROM quiz_scores")
        quiz_attempts = cur.fetchone()["c"]

        cur.execute("SELECT AVG(CAST(score as float) / NULLIF(total,0)) as avgp FROM quiz_scores")
        avgp = cur.fetchone()["avgp"]

        cur.execute("""
            SELECT score, total, created_at
            FROM quiz_scores
            ORDER BY id DESC
            LIMIT 10
        """)
        last10 = cur.fetchall()

    # ✅ USER -> only own
    else:
        cur.execute("SELECT COUNT(*) as c FROM quiz_scores WHERE user_email=?", (email,))
        quiz_attempts = cur.fetchone()["c"]

        cur.execute("SELECT AVG(CAST(score as float) / NULLIF(total,0)) as avgp FROM quiz_scores WHERE user_email=?", (email,))
        avgp = cur.fetchone()["avgp"]

        cur.execute("""
            SELECT score, total, created_at
            FROM quiz_scores
            WHERE user_email=?
            ORDER BY id DESC
            LIMIT 10
        """, (email,))
        last10 = cur.fetchall()

    conn.close()

    avg_percent = round(((avgp or 0) * 100), 2)

    quiz_last10 = []
    for r in reversed(last10):
        total = r["total"] or 0
        pct = (r["score"] / total * 100) if total else 0
        quiz_last10.append({
            "date": r["created_at"],
            "score": r["score"],
            "total": total,
            "percent": round(pct, 2),
        })

    # ---- chat stats (keep your existing code below unchanged) ----
    ...


    # -------- Chat stats from SQLAlchemy --------
    total_chats = db.query(Chat).filter(Chat.user_id == user.id).count()
    total_msgs = (
        db.query(Message)
        .join(Chat, Chat.id == Message.chat_id)
        .filter(Chat.user_id == user.id)
        .count()
    )

    # messages per day (last 30 days)
    since = datetime.utcnow() - timedelta(days=30)
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
import json

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
