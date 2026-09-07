"""
Authentication Router: Real signup, login with password hashing (bcrypt),
"Remember Me" refresh token session management, server-side CAPTCHA verification,
rate-limiting/lockout after 5 failed attempts, server-side token revocation,
password reset flow, and audit trail integration.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.core.config import settings
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    decode_token,
    verify_captcha,
    oauth2_scheme,
    get_current_user
)
from backend.app.models.transaction import User, Merchant, RevokedToken
from backend.app.models.risk_case import AuditLog
from backend.app.services.audit_chain_service import AuditChainService

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])

EMAIL_REGEX = r"^[^@]+@[^@]+\.[^@]+$"

# ----------------- Schemas -----------------
class SignupRequest(BaseModel):
    email: str = Field(..., description="Valid merchant email address")
    password: str = Field(..., min_length=8, description="Password minimum 8 characters")
    merchant_name: Optional[str] = "Primary Merchant"
    captcha_token: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, clean):
            raise ValueError("Invalid email format. Must contain '@' and domain.")
        return clean

class LoginRequest(BaseModel):
    email: Optional[str] = None
    merchant_id: Optional[str] = None
    password: str
    remember_me: bool = False
    captcha_token: Optional[str] = None

class RefreshRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, clean):
            raise ValueError("Invalid email format.")
        return clean

class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str = Field(..., min_length=8)

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    merchant_id: str
    email: Optional[str] = None
    expires_in: int

# ----------------- Helper -----------------
def _log_auth_audit(db: Session, merchant_id: str, action: str, details: str, status_str: str = "SUCCESS"):
    """Writes an immutable security event log to the BharatSHIELD audit trail."""
    try:
        log_id = f"AUTH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:18]}"
        audit = AuditLog(
            log_id=log_id,
            transaction_id=f"AUTH_{action}",
            merchant_id=merchant_id or "MER_razorpay_001",
            decision_type=f"AUTH_{action}",
            risk_score=0 if status_str == "SUCCESS" else 75,
            risk_level="LOW" if status_str == "SUCCESS" else "HIGH",
            recommended_action="ALLOW" if status_str == "SUCCESS" else "BLOCK",
            reasons_summary=f"Security Audit: {action} ({status_str}) - {details}",
            raw_payload=f'{{"action": "{action}", "status": "{status_str}", "details": "{details}"}}',
            created_at=datetime.now(timezone.utc)
        )
        AuditChainService.append_to_chain(db, audit)
        db.add(audit)
        db.commit()
    except Exception as e:
        db.rollback()

# ----------------- Endpoints -----------------

@router.post("/signup", response_model=AuthResponse, summary="Create New Merchant Account")
def signup(payload: SignupRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else None

    # 1. Verify CAPTCHA (mandatory server-side check)
    if not verify_captcha(payload.captcha_token, client_ip):
        _log_auth_audit(db, "SYSTEM", "SIGNUP", f"Blocked: Invalid CAPTCHA from {client_ip}", "FAILED")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CAPTCHA verification failed. Please complete the security challenge."
        )

    # 2. Check if email already registered
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account with this email already exists. Please log in directly."
        )

    # 3. Create or derive merchant account
    base_slug = payload.email.split("@")[0].lower()
    clean_slug = "".join([c if c.isalnum() else "_" for c in base_slug])[:16]
    merchant_id = f"MER_{clean_slug}_{int(datetime.now(timezone.utc).timestamp()) % 1000:03d}"

    merchant = Merchant(
        merchant_id=merchant_id,
        name=payload.merchant_name or f"{payload.email}'s Org",
        api_key=f"key_live_{merchant_id}_secret"
    )
    db.add(merchant)

    # 4. Hash password with bcrypt
    hashed_pwd = get_password_hash(payload.password)
    user = User(
        email=payload.email.lower(),
        hashed_password=hashed_pwd,
        merchant_id=merchant_id,
        role="admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 5. Issue access and refresh tokens
    access_token, _, access_exp = create_access_token(user.id, merchant_id=merchant_id)
    refresh_token, _, _ = create_refresh_token(user.id, merchant_id=merchant_id, remember_me=True)

    _log_auth_audit(db, merchant_id, "SIGNUP", f"New merchant registered: {user.email}", "SUCCESS")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "merchant_id": merchant_id,
        "email": user.email,
        "expires_in": int(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    }

@router.post("/login", response_model=AuthResponse, summary="Merchant Sign In with Rate Limiting")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else None
    now = datetime.now(timezone.utc)

    # 1. CAPTCHA verification
    if not verify_captcha(payload.captcha_token, client_ip):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CAPTCHA verification failed. Please complete the security challenge."
        )

    # 2. Find user (by email or merchant_id)
    identifier = (payload.email or payload.merchant_id or "").strip().lower()
    if not identifier:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or merchant_id required")

    user = db.query(User).filter(
        (User.email == identifier) | (User.merchant_id == identifier)
    ).first()

    # Legacy demo credentials fallback
    if not user and identifier in ["mer_razorpay_001", "demo@bharatshield.com", "admin@bharatshield.com"]:
        if payload.password == "demo123":
            # Auto-provision user for demo merchant
            hashed = get_password_hash("demo123")
            user = User(
                email="admin@bharatshield.com",
                hashed_password=hashed,
                merchant_id="MER_razorpay_001",
                role="admin"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    if not user:
        _log_auth_audit(db, "UNKNOWN", "LOGIN_ATTEMPT", f"Failed attempt for unknown identifier: {identifier}", "FAILED")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your email/merchant ID and password."
        )

    # 3. Check Account Lockout
    if user.locked_until:
        locked_until_utc = user.locked_until.replace(tzinfo=timezone.utc) if user.locked_until.tzinfo is None else user.locked_until
        if locked_until_utc > now:
            remaining_secs = int((locked_until_utc - now).total_seconds())
            remaining_mins = max(1, remaining_secs // 60)
            _log_auth_audit(db, user.merchant_id, "LOGIN_BLOCKED", f"Account locked: {user.email}", "FAILED")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Security lockout active due to 5 consecutive failed attempts. Please retry in {remaining_mins} minutes."
            )

    # 4. Verify password
    if not verify_password(payload.password, user.hashed_password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        
        # Trigger lockout if threshold reached
        if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=settings.LOCKOUT_MINUTES)
            db.commit()
            _log_auth_audit(db, user.merchant_id, "ACCOUNT_LOCKOUT", f"5 failed logins triggered lockout for {user.email}", "FAILED")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Maximum failed attempts exceeded. Account is temporarily locked for {settings.LOCKOUT_MINUTES} minutes."
            )
        db.commit()
        _log_auth_audit(db, user.merchant_id, "LOGIN_ATTEMPT", f"Incorrect password for {user.email} (Attempt {user.failed_login_attempts}/5)", "FAILED")
        remaining = settings.MAX_FAILED_LOGIN_ATTEMPTS - user.failed_login_attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect credentials. {remaining} attempt(s) remaining before security lockout."
        )

    # 5. Success — reset lockout & failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    # 6. Generate access & refresh tokens
    merchant_id = user.merchant_id or "MER_razorpay_001"
    access_token, _, _ = create_access_token(user.id, merchant_id=merchant_id)
    refresh_token, _, _ = create_refresh_token(user.id, merchant_id=merchant_id, remember_me=payload.remember_me)

    _log_auth_audit(db, merchant_id, "LOGIN", f"Successful login for {user.email} (RememberMe: {payload.remember_me})", "SUCCESS")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "merchant_id": merchant_id,
        "email": user.email,
        "expires_in": int(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    }

@router.post("/refresh", response_model=AuthResponse, summary="Refresh Access Token")
def refresh_session(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_data = decode_token(payload.refresh_token)
    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    jti = token_data.get("jti")
    revoked = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
    if revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session has been revoked")

    user_id = token_data.get("sub")
    merchant_id = token_data.get("merchant_id", "MER_razorpay_001")
    remember_me = token_data.get("remember_me", False)

    # Issue fresh tokens
    new_access, _, _ = create_access_token(user_id, merchant_id=merchant_id)
    new_refresh, _, _ = create_refresh_token(user_id, merchant_id=merchant_id, remember_me=remember_me)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "merchant_id": merchant_id,
        "expires_in": int(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    }

@router.post("/logout", summary="Server-side Logout & Revocation")
def logout(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        return {"status": "LOGGED_OUT", "message": "No active session"}

    token_data = decode_token(token)
    if token_data:
        jti = token_data.get("jti")
        exp = token_data.get("exp")
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else datetime.now(timezone.utc) + timedelta(days=1)
        if jti:
            revocation = RevokedToken(jti=jti, expires_at=expires_at)
            db.merge(revocation)
            db.commit()

        merchant_id = token_data.get("merchant_id", "MER_razorpay_001")
        _log_auth_audit(db, merchant_id, "LOGOUT", f"Session revoked: {jti}", "SUCCESS")

    return {"status": "LOGGED_OUT", "message": "Session invalidated server-side."}

@router.post("/forgot-password", summary="Initiate Password Recovery")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        # Avoid user enumeration by returning a uniform success message
        return {
            "status": "SENT",
            "message": "If that email is registered, recovery instructions have been sent."
        }

    reset_token = f"rst_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{user.id[:8]}"
    user.reset_token = reset_token
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    _log_auth_audit(db, user.merchant_id or "SYSTEM", "FORGOT_PASSWORD", f"Reset requested for {user.email}", "SUCCESS")

    # In dev/demo mode, provide the token in response; in prod email service would deliver it
    return {
        "status": "SENT",
        "message": "Password reset token generated (valid for 1 hour).",
        "dev_reset_token": reset_token if settings.DEBUG else None
    }

@router.post("/reset-password", summary="Complete Password Reset")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    user = db.query(User).filter(User.reset_token == payload.reset_token).first()
    if not user or not user.reset_token_expires_at or user.reset_token_expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token."
        )

    user.hashed_password = get_password_hash(payload.new_password)
    user.reset_token = None
    user.reset_token_expires_at = None
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    _log_auth_audit(db, user.merchant_id or "SYSTEM", "PASSWORD_RESET", f"Password changed for {user.email}", "SUCCESS")

    return {"status": "SUCCESS", "message": "Password updated successfully. You may now log in."}

@router.get("/me", summary="Current Authenticated User Profile")
def get_me(user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = user_data.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    merchant_id = user_data.get("merchant_id", "MER_razorpay_001")
    merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()

    return {
        "user_id": user_id,
        "email": user.email if user else None,
        "role": user.role if user else "analyst",
        "merchant_id": merchant_id,
        "merchant_name": merchant.name if merchant else "Merchant Org",
        "created_at": user.created_at.isoformat() if user and user.created_at else None
    }
