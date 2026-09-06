"""
Authentication router providing demo login and API token generation.
"""

from datetime import timedelta
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, status
from backend.app.core.security import create_access_token
from backend.app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    merchant_id: str = "MER_razorpay_001"
    password: str = "demo123"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    merchant_id: str

@router.post("/login", response_model=TokenResponse, summary="Demo Merchant Login")
def login(payload: LoginRequest):
    # Demo credentials validation
    if payload.password != "demo123":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials. For demo, use 'demo123'."
        )
    token = create_access_token(
        subject=payload.merchant_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "merchant_id": payload.merchant_id
    }
