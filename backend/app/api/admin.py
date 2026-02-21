# backend/app/api/admin.py

import os, json, sqlite3, shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from app.models import Feedback
from app.models import QuizScore  # ⚠️ if your model name differs, change here
from app.database import get_db
from app.models import User, Chat, Message
from app.auth import require_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# ✅ SAME health.db path like quiz.py / feedback.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # backend/app
DB_PATH = os.path.join(BASE_DIR, "health.db")

# ✅ PDF folder + ingest state file
PDF_DIR = os.path.join(BASE_DIR, "data", "medical_pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

STATE_PATH = os.path.join(BASE_DIR, "data", "ingest_state.json")
os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)


# -----------------------
# Helpers for Smart Ingest
# -----------------------
def load_state():
    if not os.path.exists(STATE_PATH):
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump({"files": {}}, f)
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# -----------------------
# Get All Users
# -----------------------
@router.get("/users")
def get_all_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
        }
        for u in users
    ]


# -----------------------
# Block / Unblock User
# -----------------------
@router.patch("/users/{user_id}/block")
def toggle_user_block(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "ADMIN":
        raise HTTPException(status_code=400, detail="Cannot block another admin")

    user.is_active = not user.is_active
    db.commit()
    return {"message": "User status updated", "is_active": user.is_active}


# -----------------------
# Change Role (USER <-> ADMIN)
# -----------------------
@router.patch("/users/{user_id}/role")
def change_role(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot change your own role")

    user.role = "ADMIN" if user.role == "USER" else "USER"
    db.commit()
    return {"message": "Role updated", "new_role": user.role}


# -----------------------
# Dashboard Stats
# -----------------------
@router.get("/stats")
def admin_stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_chats = db.query(func.count(Chat.id)).scalar() or 0
    total_messages = db.query(func.count(Message.id)).scalar() or 0

    return {
        "total_users": total_users,
        "total_chats": total_chats,
        "total_messages": total_messages,
    }

# -----------------------
# Admin: Quiz History (All Users)
# -----------------------
@router.get("/quiz-history")
def all_quiz_history(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    rows = db.query(QuizScore).order_by(QuizScore.id.desc()).limit(500).all()
    return [
        {
            "id": r.id,
            "user_email": getattr(r, "user_email", None),
            "score": getattr(r, "score", None),
            "total": getattr(r, "total", None),
            "created_at": r.created_at.isoformat() if getattr(r, "created_at", None) else None,
        }
        for r in rows
    ]


@router.delete("/quiz-history/{row_id}")
def delete_quiz_row(row_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    r = db.query(QuizScore).filter(QuizScore.id == row_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Quiz row not found")
    db.delete(r)
    db.commit()
    return {"ok": True, "message": "Quiz deleted"}


# -----------------------
# Admin: Feedback History (All Users)
# -----------------------
@router.get("/feedback-history")
def all_feedback_history(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    rows = db.query(Feedback).order_by(Feedback.id.desc()).limit(500).all()
    return [
        {
            "id": r.id,
            "user_email": getattr(r, "user_email", None),
            "rating": getattr(r, "rating", None),
            "category": getattr(r, "category", None),
            "message": getattr(r, "message", None),
            "created_at": r.created_at.isoformat() if getattr(r, "created_at", None) else None,
        }
        for r in rows
    ]


class FeedbackUpdate(BaseModel):
    rating: int
    category: str
    message: str


@router.patch("/feedback-history/{row_id}")
def update_feedback_row(row_id: int, data: FeedbackUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    r = db.query(Feedback).filter(Feedback.id == row_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Feedback row not found")

    r.rating = data.rating
    r.category = data.category
    r.message = data.message
    db.commit()
    db.refresh(r)
    return {"ok": True, "message": "Feedback updated"}


@router.delete("/feedback-history/{row_id}")
def delete_feedback_row(row_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    r = db.query(Feedback).filter(Feedback.id == row_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Feedback row not found")
    db.delete(r)
    db.commit()
    return {"ok": True, "message": "Feedback deleted"}

    



# -----------------------
# Admin: PDF List
# -----------------------
@router.get("/pdfs")
def list_pdfs(admin: User = Depends(require_admin)):
    files = []
    for fn in os.listdir(PDF_DIR):
        if fn.lower().endswith(".pdf"):
            files.append({"filename": fn})
    files.sort(key=lambda x: x["filename"])
    return {"ok": True, "files": files}


# -----------------------
# Admin: PDF Upload
# -----------------------
@router.post("/pdfs/upload")
def upload_pdf(file: UploadFile = File(...), admin: User = Depends(require_admin)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF allowed")

    save_path = os.path.join(PDF_DIR, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"ok": True, "message": "PDF uploaded", "filename": file.filename}


# -----------------------
# Admin: PDF Delete
# -----------------------
@router.delete("/pdfs/{filename}")
def delete_pdf(filename: str, admin: User = Depends(require_admin)):
    path = os.path.join(PDF_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="PDF not found")

    os.remove(path)

    # also remove from ingest_state if present
    state = load_state()
    done = state.get("files", {})
    if filename in done:
        done.pop(filename, None)
        state["files"] = done
        save_state(state)

    return {"ok": True, "message": "PDF deleted"}


# -----------------------
# Admin: SMART PDF INGEST (only new/updated)
# -----------------------
@router.post("/pdfs/ingest")
def ingest_pdfs(admin: User = Depends(require_admin)):
    """
    ✅ Smart ingest:
    - Already indexed PDFs are skipped (based on mtime)
    - Only new/updated PDFs are ingested
    """
    try:
        from app.rag.ingest import ingest_folder_to_pinecone
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import ingest failed: {str(e)}")

    state = load_state()
    done = state.get("files", {})

    pdfs = [fn for fn in os.listdir(PDF_DIR) if fn.lower().endswith(".pdf")]
    if not pdfs:
        return {"ok": True, "message": "No PDFs found", "processed": 0, "skipped": 0, "processed_files": []}

    to_process = []
    skipped = 0

    for fn in pdfs:
        path = os.path.join(PDF_DIR, fn)
        mtime = int(os.path.getmtime(path))
        prev = done.get(fn)

        if prev and prev.get("mtime") == mtime:
            skipped += 1
            continue

        to_process.append(fn)

    if not to_process:
        return {"ok": True, "message": "No new PDFs to ingest", "processed": 0, "skipped": skipped, "processed_files": []}

    # ✅ ingest ONLY these PDFs
    result = ingest_folder_to_pinecone(file_list=to_process)

    # If any file failed -> don't mark as done
    if not result.get("ok"):
        return {
            "ok": False,
            "message": "Ingest failed for some files",
            "processed": result.get("processed", 0),
            "skipped": skipped,
            "processed_files": result.get("processed_files", []),
            "failed": result.get("failed", []),
            "ingest_result": result,
        }

    # ✅ update state only for processed_files
    processed_files = result.get("processed_files", [])
    for fn in processed_files:
        path = os.path.join(PDF_DIR, fn)
        if os.path.exists(path):
            done[fn] = {"mtime": int(os.path.getmtime(path))}

    state["files"] = done
    save_state(state)

    return {
        "ok": True,
        "message": "Smart ingest completed",
        "processed": len(processed_files),
        "skipped": skipped,
        "processed_files": processed_files,
        "ingest_result": result
    }