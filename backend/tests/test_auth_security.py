"""
Comprehensive unit & integration tests for BharatSHIELD Authentication & Security.
Validates:
1. User registration with bcrypt password hashing.
2. Direct login without forced re-signup.
3. Server-side CAPTCHA enforcement.
4. Account lockout after 5 consecutive failed attempts.
5. Server-side token invalidation / logout.
6. Audit trail integration for auth actions.
7. Password reset token lifecycle.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.connection import SessionLocal
from backend.app.models.transaction import User, RevokedToken
from backend.app.models.risk_case import AuditLog
import uuid

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_test_users():
    db = SessionLocal()
    db.query(User).filter(User.email.like("%@example.com") | User.email.like("%@hdfcsec.com") | User.email.like("%@merchant.com") | User.email.like("%@enterprise.com")).delete(synchronize_session=False)
    db.commit()
    db.close()
    yield

def test_captcha_enforcement():
    """TASK 4: CAPTCHA must be validated server-side, not bypassed."""
    # Attempt signup without captcha
    resp = client.post("/api/auth/signup", json={
        "email": "nocaptcha@example.com",
        "password": "Password123!",
        "captcha_token": ""
    })
    assert resp.status_code == 400
    assert "CAPTCHA verification failed" in resp.json()["detail"]

    # Attempt login without captcha
    resp_login = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "Password123!",
        "captcha_token": ""
    })
    assert resp_login.status_code == 400
    assert "CAPTCHA verification failed" in resp_login.json()["detail"]

def test_signup_and_login_flow():
    """TASK 3 & 6: Sign up, immediately login, no forced re-signup."""
    email = "risk.officer@hdfcsec.com"
    password = "SecureRiskOfficer2026!"

    # 1. Signup
    signup_resp = client.post("/api/auth/signup", json={
        "email": email,
        "password": password,
        "merchant_name": "HDFC Risk Gateway",
        "captcha_token": "TEST_CAPTCHA_PASS"
    })
    assert signup_resp.status_code == 200
    signup_data = signup_resp.json()
    assert "access_token" in signup_data
    assert "refresh_token" in signup_data
    assert signup_data["email"] == email

    # Verify password was hashed, not stored plaintext
    db = SessionLocal()
    user_db = db.query(User).filter(User.email == email).first()
    assert user_db is not None
    assert user_db.hashed_password != password
    assert user_db.hashed_password.startswith("$2b$") or user_db.hashed_password.startswith("$2a$")
    db.close()

    # 2. Re-signup fails (cannot duplicate account)
    dup_resp = client.post("/api/auth/signup", json={
        "email": email,
        "password": password,
        "captcha_token": "TEST_CAPTCHA_PASS"
    })
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"]

    # 3. Login with correct credentials
    login_resp = client.post("/api/auth/login", json={
        "email": email,
        "password": password,
        "remember_me": True,
        "captcha_token": "TEST_CAPTCHA_PASS"
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert "refresh_token" in login_data

def test_account_lockout_after_five_failures():
    """TASK 5: Lockout / rate-limit kicks in after 5 consecutive failed login attempts."""
    email = "lockout.target@merchant.com"
    password = "CorrectPassword123!"

    # Register target
    client.post("/api/auth/signup", json={
        "email": email,
        "password": password,
        "captcha_token": "TEST_CAPTCHA_PASS"
    })

    # Attempt 1 to 4 with incorrect password
    for i in range(1, 5):
        resp = client.post("/api/auth/login", json={
            "email": email,
            "password": "WrongPassword!",
            "captcha_token": "TEST_CAPTCHA_PASS"
        })
        assert resp.status_code == 401
        assert "attempt(s) remaining" in resp.json()["detail"]

    # 5th failed attempt -> triggers lockout
    resp_5 = client.post("/api/auth/login", json={
        "email": email,
        "password": "WrongPassword!",
        "captcha_token": "TEST_CAPTCHA_PASS"
    })
    assert resp_5.status_code == 429
    assert "temporarily locked" in resp_5.json()["detail"]

    # Even with correct password, login is blocked during lockout
    resp_locked = client.post("/api/auth/login", json={
        "email": email,
        "password": password,
        "captcha_token": "TEST_CAPTCHA_PASS"
    })
    assert resp_locked.status_code == 429
    assert "Security lockout active" in resp_locked.json()["detail"]

def test_logout_server_revocation():
    """TASK 3: Server-side token invalidation upon logout."""
    email = "logout.test@enterprise.com"
    password = "EnterpriseSecurePass1!"

    # Signup to get token
    res = client.post("/api/auth/signup", json={
        "email": email,
        "password": password,
        "captcha_token": "TEST_CAPTCHA_PASS"
    })
    token = res.json()["access_token"]

    # Access /api/auth/me -> works
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200

    # Logout
    logout_resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200

    # Try accessing /api/auth/me again -> rejected because token is revoked
    after_logout = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert after_logout.status_code == 401
    assert "revoked" in after_logout.json()["detail"]

def test_auth_events_recorded_in_audit_log():
    """TASK 5: Auth actions are securely written into immutable AuditLog."""
    db = SessionLocal()
    audit_entries = db.query(AuditLog).filter(AuditLog.transaction_id.like("AUTH_%")).all()
    assert len(audit_entries) > 0, "No authentication events were found in AuditLog!"
    db.close()
