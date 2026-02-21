from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app import models

from app.routes_auth import router as auth_router
from app.routes_chat import router as chat_router
# from app.api.faq import router as faq_router
from app.api.diseases import router as diseases_router
from app.api.symptom_checker import router as symptom_router
from app.api.quiz import router as quiz_router
from app.api.reports import router as reports_router
from app.api.feedback import router as feedback_router
from app.api.ml_prediction import router as ml_router
from app.api.admin import router as admin_router

# ✅ create tables
Base.metadata.create_all(bind=engine)
from sqlalchemy import text

# ✅ AUTO DB MIGRATION (timezone fix)
with engine.connect() as conn:
    try:
        conn.execute(text("""
        ALTER TABLE feedback
          ALTER COLUMN created_at TYPE TIMESTAMPTZ
          USING created_at AT TIME ZONE 'UTC'
        """))
    except:
        pass

    try:
        conn.execute(text("""
        ALTER TABLE quiz_scores
          ALTER COLUMN created_at TYPE TIMESTAMPTZ
          USING created_at AT TIME ZONE 'UTC'
        """))
    except:
        pass
# ✅ CREATE APP FIRST
app = FastAPI(title="AI Health Assistant API")

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set([
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://aihealth-assistant-finalbot.vercel.app",
        "https://ai-chatbot-five-sandy-46.vercel.app",
        settings.FRONTEND_BASE_URL,
    ])),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ REQUIRED for Google OAuth (Authlib uses session for state)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET,
    same_site="none",
    https_only=True,
)

# ✅ INCLUDE ROUTERS AFTER app CREATED
app.include_router(auth_router)
app.include_router(chat_router)

app.include_router(diseases_router)
app.include_router(symptom_router)

app.include_router(quiz_router)
app.include_router(reports_router)
app.include_router(feedback_router)
app.include_router(ml_router)
# app.include_router(faq_router)
app.include_router(admin_router)

@app.get("/")
def root():
    return {"message": "API running"}