# app/routes_auth.py

from datetime import datetime, timedelta
import secrets
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from authlib.integrations.starlette_client import OAuth, OAuthError
from pydantic import BaseModel

from app.database import get_db
from app.models import User, PasswordReset
from app.schemas import UserCreate, UserLogin, UserOut
from app.auth import hash_password, verify_password, create_access_token
from app.config import settings
from app.utils.mailer import send_email

router = APIRouter(prefix="/auth", tags=["Auth"])


# ======================================================
# ✅ Forgot Password Schemas
# ======================================================
class ForgotPasswordIn(BaseModel):
    email: str


class ResetPasswordIn(BaseModel):
    email: str
    otp: str
    new_password: str
    confirm_password: str


def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


# -----------------------
# Normal Signup
# -----------------------
@router.post("/signup", response_model=UserOut)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == user.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    # ✅ bcrypt max password bytes = 72
    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password too long (max 72 characters)")

    admin_email = (getattr(settings, "ADMIN_EMAIL", "") or "").strip().lower()
    role = "ADMIN" if user.email.strip().lower() == admin_email and admin_email else "USER"

    new_user = User(
        full_name=user.full_name,
        email=user.email.strip().lower(),
        password=hash_password(user.password),
        role=role,
        is_active=True,
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except SQLAlchemyError as e:
        db.rollback()
        print("DB ERROR:", str(e))
        raise HTTPException(status_code=500, detail="Database error during signup")

    return new_user


# -----------------------
# Normal Login
# -----------------------
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # ✅ if blocked by admin
    if hasattr(db_user, "is_active") and db_user.is_active is False:
        raise HTTPException(status_code=403, detail="Your account is blocked. Contact admin.")

    token = create_access_token(
        {
            "id": db_user.id,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "role": getattr(db_user, "role", "USER"),
        }
    )
    return {"access_token": token, "token_type": "bearer"}


# ======================================================
# ✅ Forgot Password (OTP)
# ======================================================
@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordIn, db: Session = Depends(get_db)):
    email = (body.email or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        # ✅ Security: don't reveal if user exists
        return {"message": "If account exists, OTP sent to email."}

    otp = f"{secrets.randbelow(900000) + 100000}"  # 6 digits
    otp_hash = _hash_otp(otp)
    expires_at = datetime.utcnow() + timedelta(minutes=settings.RESET_OTP_EXPIRE_MINUTES)

    # ✅ mark old OTPs as used
    try:
        db.query(PasswordReset).filter(
            PasswordReset.email == email,
            PasswordReset.used == False
        ).update({"used": True})
        db.commit()
    except Exception as e:
        db.rollback()
        print("RESET UPDATE ERROR:", e)

    pr = PasswordReset(
        email=email,
        otp_hash=otp_hash,
        expires_at=expires_at,
        used=False
    )

    try:
        db.add(pr)
        db.commit()
    except Exception as e:
        db.rollback()
        print("RESET INSERT ERROR:", e)
        raise HTTPException(status_code=500, detail="Database error")

    reset_link = f"{settings.FRONTEND_BASE_URL}/reset_password.html?email={email}"

    body_text = f"""Hi {user.full_name},

Your password reset OTP is: {otp}
This OTP is valid for {settings.RESET_OTP_EXPIRE_MINUTES} minutes.

Reset link:
{reset_link}

If you did not request this, ignore this email.
"""

    try:
        send_email(email, "HealthBot AI - Password Reset OTP", body_text)
    except Exception as e:
        print("EMAIL ERROR:", e)
        raise HTTPException(status_code=500, detail="Failed to send email")

    return {"message": "If account exists, OTP sent to email."}


@router.post("/reset-password")
def reset_password(body: ResetPasswordIn, db: Session = Depends(get_db)):
    email = (body.email or "").strip().lower()
    otp = (body.otp or "").strip()

    if not email or not otp:
        raise HTTPException(status_code=400, detail="Email and OTP required")

    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    if len(body.new_password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password too long (max 72 characters)")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid request")

    pr = (
        db.query(PasswordReset)
        .filter(PasswordReset.email == email, PasswordReset.used == False)
        .order_by(PasswordReset.id.desc())
        .first()
    )

    if not pr:
        raise HTTPException(status_code=400, detail="OTP not found")

    if datetime.utcnow() > pr.expires_at:
        pr.used = True
        db.commit()
        raise HTTPException(status_code=400, detail="OTP expired")

    if _hash_otp(otp) != pr.otp_hash:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # ✅ success
    user.password = hash_password(body.new_password)
    pr.used = True
    db.commit()

    return {"message": "Password reset successful. Please login."}


# ======================================================
# ✅ GOOGLE OAUTH (Functional)
# ======================================================
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/google/login")
async def google_login(request: Request):
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        print("GOOGLE OAUTH ERROR:", e)
        # ✅ temporary browser debug
        return PlainTextResponse(f"Google OAuth Error: {str(e)}", status_code=400)

    userinfo = token.get("userinfo")
    if not userinfo:
        userinfo = await oauth.google.userinfo(token=token)

    email = userinfo.get("email")
    name = userinfo.get("name") or "Google User"

    if not email:
        return RedirectResponse(f"{settings.FRONTEND_BASE_URL}/login.html?error=no_email")

    # Upsert user
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        admin_email = (getattr(settings, "ADMIN_EMAIL", "") or "").strip().lower()
        role = "ADMIN" if email.strip().lower() == admin_email and admin_email else "USER"

        db_user = User(
            full_name=name,
            email=email.strip().lower(),
            password=hash_password(email),
            role=role,
            is_active=True,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    # ✅ blocked?
    if hasattr(db_user, "is_active") and db_user.is_active is False:
        return RedirectResponse(f"{settings.FRONTEND_BASE_URL}/login.html?error=blocked")

    # Create JWT and redirect to frontend with token
    jwt_token = create_access_token(
        {
            "id": db_user.id,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "role": getattr(db_user, "role", "USER"),
        }
    )

    return RedirectResponse(
        f"{settings.FRONTEND_BASE_URL}/oauth-success.html?token={jwt_token}",
        status_code=302,
    )