# backend/app/api/feedback.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import sqlite3, os
from datetime import datetime, timezone

from app.auth import get_current_user

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # backend/app
DB_PATH = os.path.join(BASE_DIR, "health.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1) ensure table exists (basic)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT
        )
    """)

    # 2) read existing columns
    cur.execute("PRAGMA table_info(feedback)")
    cols = {row[1] for row in cur.fetchall()}  # column names

    # 3) add missing columns safely
    if "user_email" not in cols:
        cur.execute("ALTER TABLE feedback ADD COLUMN user_email TEXT")
    if "rating" not in cols:
        cur.execute("ALTER TABLE feedback ADD COLUMN rating INTEGER")
    if "category" not in cols:
        cur.execute("ALTER TABLE feedback ADD COLUMN category TEXT")
    if "message" not in cols:
        cur.execute("ALTER TABLE feedback ADD COLUMN message TEXT")
    if "created_at" not in cols:
        cur.execute("ALTER TABLE feedback ADD COLUMN created_at TEXT")

    conn.commit()
    conn.close()


class FeedbackIn(BaseModel):
    rating: int
    category: str = "general"
    message: str


@router.post("/submit")
def submit_feedback(body: FeedbackIn, user=Depends(get_current_user)) -> Dict[str, Any]:
    init_db()

    if body.rating < 1 or body.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1 to 5")

    msg = (body.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Message is empty")

    email = getattr(user, "email", None) or getattr(user, "username", None) or "unknown"

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO feedback (user_email, rating, category, message, created_at) VALUES (?,?,?,?,?)",
        (
            email,
            int(body.rating),
            (body.category or "general"),
            msg,
            datetime.now(timezone.utc).isoformat(),  # ✅ timezone-aware UTC
        ),
    )
    conn.commit()
    conn.close()

    return {"ok": True, "message": "submitted"}


@router.get("/my")
def my_feedback(user=Depends(get_current_user)):
    init_db()

    email = getattr(user, "email", None) or getattr(user, "username", "unknown")
    role = getattr(user, "role", "USER")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if role == "ADMIN":
        cur.execute("SELECT * FROM feedback ORDER BY id DESC")
    else:
        cur.execute(
            "SELECT * FROM feedback WHERE user_email=? ORDER BY id DESC",
            (email,),
        )

    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]