# app/routes_chat.py

import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, Chat, Message, Document
from app.schemas import (
    ChatCreateOut,
    ChatListOut,
    ChatRenameIn,
    ChatSendIn,
    ChatSendOut,
    MessageOut,
)

from app.services.openrouter_client import (
    openrouter_chat,
    is_medical_query_openrouter,
    generate_chat_title,
)

from app.rag.vectorstore import (
    upsert_document_to_chat,
    retrieve_context_for_chat,
    retrieve_context_from_namespace,
)

from app.config import settings

router = APIRouter(prefix="/chat", tags=["Chat"])
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


# -----------------------
# helper: detect doc-related question
# -----------------------
def is_doc_question(t: str) -> bool:
    t = (t or "").lower()
    doc_words = [
        "this pdf", "in this pdf", "from this pdf",
        "this file", "in this file", "from this file",
        "this document", "in this document", "from this document",
        "this image", "in this image", "from this image",
        "this photo", "in this photo", "from this photo",
        "uploaded file", "uploaded", "upload", "attachment",
        "above image", "given image",
        "extract", "summarize", "summary", "explain this",
        "what is written", "what does it say",
        "medicine name", "tablet name", "drug name",
    ]
    return any(w in t for w in doc_words)


# -----------------------
# Create New Chat
# -----------------------
@router.post("/new", response_model=ChatCreateOut)
def new_chat(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = Chat(
        user_id=user.id,
        title="New Chat",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)

    welcome = "Hi! I’m your AI Health Assistant. Ask me about symptoms, diseases, prevention, diet, and healthy habits."

    db.add(
        Message(
            chat_id=chat.id,
            role="assistant",
            content=welcome,
            created_at=datetime.utcnow(),
        )
    )
    db.commit()

    return {"id": chat.id, "title": chat.title}


# -----------------------
# List Chats
# -----------------------
@router.get("/list", response_model=list[ChatListOut])
def list_chats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chats = (
        db.query(Chat)
        .filter(Chat.user_id == user.id)
        .order_by(Chat.updated_at.desc())
        .all()
    )
    return [{"id": c.id, "title": c.title, "updated_at": c.updated_at.isoformat()} for c in chats]


# -----------------------
# Get Messages
# -----------------------
@router.get("/{chat_id}/messages", response_model=list[MessageOut])
def get_messages(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    msgs = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in msgs
    ]


# -----------------------
# Rename Chat
# -----------------------
@router.post("/{chat_id}/rename")
def rename_chat(chat_id: int, body: ChatRenameIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat.title = body.title.strip()[:60] if body.title else "Chat"
    chat.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


# -----------------------
# Delete Chat
# -----------------------
@router.delete("/{chat_id}")
def delete_chat(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    db.delete(chat)
    db.commit()
    return {"ok": True}


# -----------------------
# Share Chat
# -----------------------
@router.post("/{chat_id}/share")
def share_chat(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if not chat.share_id:
        chat.share_id = str(uuid.uuid4())
        db.commit()

    return {"share_id": chat.share_id}


# -----------------------
# Upload File to Chat
# -----------------------
@router.post("/{chat_id}/upload")
async def upload_file(
    chat_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".txt", ".md", ".png", ".jpg", ".jpeg"]:
        raise HTTPException(status_code=400, detail="Only pdf/txt/md/png/jpg allowed")

    safe_name = f"{chat_id}_{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    doc = Document(
        chat_id=chat_id,
        filename=file.filename,
        path=save_path,
        created_at=datetime.utcnow(),
    )
    db.add(doc)
    db.commit()

    # ✅ index into chat namespace
    # If image -> OCR -> create .txt -> upsert txt for RAG
    # ✅ index into chat namespace
    if ext in [".png", ".jpg", ".jpeg"]:
        try:
            from app.utils.ocr import extract_text_from_image
            ocr_text = extract_text_from_image(save_path)

            txt_path = save_path + ".txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(ocr_text or "")

            # ✅ IMPORTANT: always upsert TXT only
            upsert_document_to_chat(chat_id=chat_id, filepath=txt_path)

        except Exception:
            # if OCR fails still create txt and upsert empty
            txt_path = save_path + ".txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("")
            upsert_document_to_chat(chat_id=chat_id, filepath=txt_path)

    else:
        upsert_document_to_chat(chat_id=chat_id, filepath=save_path)


    chat.updated_at = datetime.utcnow()
    db.commit()

    return {"ok": True, "filename": file.filename}


# -----------------------
# Send Message (Classifier + RAG + Fallback)
# -----------------------
@router.post("/{chat_id}/send", response_model=ChatSendOut)
async def send_message(
    chat_id: int,
    body: ChatSendIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    user_text = (body.message or "").strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Message is empty")

    # ✅ save user message
    db.add(
        Message(
            chat_id=chat_id,
            role="user",
            content=user_text,
            created_at=datetime.utcnow(),
        )
    )
    db.commit()

    # ✅ 1) Medical intent classifier
    medical = await is_medical_query_openrouter(user_text)

    has_docs = db.query(Document).filter(Document.chat_id == chat_id).first()
    doc_q = is_doc_question(user_text)

    # ✅ PRIORITY: If user asks about uploaded doc/image -> allow even if classifier says NO
    if has_docs and doc_q:
        medical = True

    # ✅ If still non-medical -> block
    if not medical:
        bot_text = (
            "⚠️ I am a medical awareness assistant.\n"
            "Ask health/medicine questions.\n"
            
        )
        db.add(Message(chat_id=chat_id, role="assistant", content=bot_text, created_at=datetime.utcnow()))
        chat.updated_at = datetime.utcnow()
        db.commit()
        return {"reply": bot_text, "chat_title": chat.title, "updated_at": chat.updated_at.isoformat()}


    # ✅ 2) RAG context: global + chat
    context_chat = retrieve_context_for_chat(chat_id=chat_id, query=user_text)

# ✅ If uploaded doc context exists → use ONLY that
    if context_chat:
        context = context_chat
    else:
        global_ns = getattr(settings, "PINECONE_NAMESPACE", "global-medical")
        context = retrieve_context_from_namespace(namespace=global_ns, query=user_text)


    # ✅ 3) chat history (last 10)
    last_msgs = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .limit(10)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in last_msgs]

    lang = body.language or "en"

    # ✅ 4) Generate answer (RAG->NO_CONTEXT->fallback)
    bot_text = await openrouter_chat(
        model=settings.OPENROUTER_MODEL,
        user_message=user_text,
        chat_history=history,
        rag_context=context,
        language=lang,
    )

    db.add(
        Message(
            chat_id=chat_id,
            role="assistant",
            content=bot_text,
            created_at=datetime.utcnow(),
        )
    )

    # ✅ 5) server-side title generation
    if chat.title == "New Chat":
        chat.title = await generate_chat_title(user_text)

    chat.updated_at = datetime.utcnow()
    db.commit()

    return {
        "reply": bot_text,
        "chat_title": chat.title,
        "updated_at": chat.updated_at.isoformat(),
    }
