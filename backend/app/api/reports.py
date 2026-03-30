from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Float
from datetime import datetime, timedelta
import random

from app.auth import get_current_user
from app.database import get_db
from app.models import Chat, Message, QuizScore  # SQLAlchemy model

router = APIRouter(prefix="/api/reports", tags=["Reports"])

# --- Full quiz categories from first version ---
quiz_data = {
    "Infectious Diseases": [
        {"question":"Dengue spreads by?","options":["Housefly","Mosquito","Water","Food"],"answer":1},
        {"question":"COVID affects mainly?","options":["Heart","Lungs","Kidney","Liver"],"answer":1},
        {"question":"Malaria caused by?","options":["Virus","Bacteria","Parasite","Fungus"],"answer":2},
        {"question":"Flu spreads via?","options":["Water","Air droplets","Food","Soil"],"answer":1},
        {"question":"Common symptom of infection?","options":["Fever","Hair fall","Blindness","Fracture"],"answer":0},
        {"question":"TB affects?","options":["Lungs","Heart","Brain","Skin"],"answer":0},
        {"question":"Prevention of infections?","options":["Handwash","Sleep less","Skip food","None"],"answer":0},
        {"question":"Hepatitis affects?","options":["Liver","Kidney","Heart","Brain"],"answer":0},
        {"question":"Virus spreads by?","options":["Contact","Magic","Nothing","Stone"],"answer":0},
        {"question":"Immunity helps?","options":["Fight disease","Increase weight","Reduce height","None"],"answer":0}
    ],
    "Respiratory Diseases": [
        {"question":"Pneumonia affects?","options":["Lungs","Heart","Brain","Kidney"],"answer":0},
        {"question":"Asthma symptom?","options":["Breathing issue","Hair loss","Blindness","None"],"answer":0},
        {"question":"Oxygen used by?","options":["Lungs","Kidney","Liver","Skin"],"answer":0},
        {"question":"Bronchitis is?","options":["Lung issue","Bone issue","Skin issue","Eye issue"],"answer":0},
        {"question":"Cough indicates?","options":["Resp issue","Bone issue","Eye issue","None"],"answer":0},
        {"question":"Smoking affects?","options":["Lungs","Hair","Nails","None"],"answer":0},
        {"question":"Air pollution causes?","options":["Resp problems","Good health","Nothing","Sleep"],"answer":0},
        {"question":"Breathing organ?","options":["Lungs","Heart","Brain","Liver"],"answer":0},
        {"question":"Oxygen exchange?","options":["Lungs","Kidney","Skin","Hair"],"answer":0},
        {"question":"Respiratory disease example?","options":["Asthma","Diabetes","Cancer","Ulcer"],"answer":0}
    ],
    # ... include all other categories exactly like first version ...
    "Digestive Diseases": [...],
    "Chronic Diseases": [...],
    "Heart Diseases": [...],
    "Neurological Disorders": [...],
    "Skin Diseases": [...],
    "Kidney Diseases": [...],
    "Liver Diseases": [...],
    "Mental Health": [...]
}

@router.get("/summary")
def reports_summary(user=Depends(get_current_user), db: Session = Depends(get_db)):
    email = getattr(user, "email", None) or getattr(user, "username", None) or "unknown"
    role = getattr(user, "role", "USER")

    # -------------------------
    # ✅ QUIZ STATS (SQLAlchemy)
    # -------------------------
    q = db.query(QuizScore)
    if role != "ADMIN":
        q = q.filter(QuizScore.user_email == email)

    quiz_attempts = q.count()
    avgp = (
        q.with_entities(func.avg(cast(QuizScore.score, Float) / func.nullif(QuizScore.total, 0)))
        .scalar()
    )
    avg_percent = round(((avgp or 0) * 100), 2)

    # last 10 attempts
    last10 = q.order_by(QuizScore.id.desc()).limit(10).all()
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
    # ✅ CHAT STATS
    # -------------------------
    if role == "ADMIN":
        total_chats = db.query(Chat).count()
        total_msgs = db.query(Message).count()
        msgs = db.query(Message.created_at).filter(Message.created_at >= datetime.utcnow() - timedelta(days=30)).all()
        user_count = db.query(Message).filter(Message.role == "user").count()
        assistant_count = db.query(Message).filter(Message.role == "assistant").count()
    else:
        total_chats = db.query(Chat).filter(Chat.user_id == user.id).count()
        total_msgs = db.query(Message).join(Chat, Chat.id == Message.chat_id).filter(Chat.user_id == user.id).count()
        since = datetime.utcnow() - timedelta(days=30)
        msgs = db.query(Message.created_at).join(Chat, Chat.id == Message.chat_id).filter(Chat.user_id == user.id, Message.created_at >= since).all()
        user_count = db.query(Message).join(Chat, Chat.id == Message.chat_id).filter(Chat.user_id == user.id, Message.role == "user").count()
        assistant_count = db.query(Message).join(Chat, Chat.id == Message.chat_id).filter(Chat.user_id == user.id, Message.role == "assistant").count()

    # messages per day
    per_day = {}
    for (dt,) in msgs:
        key = dt.date().isoformat()
        per_day[key] = per_day.get(key, 0) + 1

    # -------------------------
    # ✅ RETURN MERGED STATS
    # -------------------------
    return {
        "kpis": {
            "quiz_attempts": quiz_attempts,
            "avg_quiz_percent": avg_percent,
            "total_chats": total_chats,
            "total_messages": total_msgs
        },
        "quiz_last10": quiz_last10,
        "messages_per_day": per_day,
        "role_ratio": {"user": user_count, "assistant": assistant_count},
        "quiz_categories": list(quiz_data.keys())  # ✅ all categories from first version
    }