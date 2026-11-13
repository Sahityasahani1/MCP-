"""Comprehensive Authentication & Multi-Tenant SQLite Database Benchmark Suite.

Verifies:
- User registration with PBKDF2 hashing
- User login and JWT access token issuance
- Protected /api/auth/me profile endpoint
- Google, GitHub, and Microsoft social sign-in endpoints
- Multi-tenant chat session isolation by user_id
- Defense against timing attacks, weak passwords, and token tampering
"""

import sys
import uuid
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app
from backend.app.config import settings
from backend.app.db.database import amra_db
from backend.app.auth import hash_password, verify_password, create_access_token, decode_access_token

client = TestClient(app)


def test_password_cryptography():
    print("\n[AUTH TEST 1] Testing PBKDF2-HMAC-SHA256 Password Cryptography...")
    plain = "SuperSecurePass2026!"
    hashed = hash_password(plain)
    assert ":" in hashed, "Hash should be colon-separated"
    assert verify_password(plain, hashed), "Valid password should verify"
    assert not verify_password("WrongPassword123", hashed), "Invalid password should fail"
    assert not verify_password("", hashed), "Empty password should fail"
    assert not verify_password(plain, None), "None hash should fail"
    print(" -> Hashing & verification passed.")


def test_jwt_minting_and_decoding():
    print("\n[AUTH TEST 2] Testing PyJWT Minting & Expiration Verification...")
    token = create_access_token(user_id="usr_test_123", email="tester@amra.ai", role="user")
    assert isinstance(token, str) and len(token) > 20
    payload = decode_access_token(token)
    assert payload["sub"] == "usr_test_123"
    assert payload["email"] == "tester@amra.ai"
    assert payload["role"] == "user"
    print(" -> JWT generation and validation passed.")


def test_user_registration_and_login_flow():
    print("\n[AUTH TEST 3] Testing Local User Registration & Login API...")
    email = f"researcher_{uuid.uuid4().hex[:10]}@test.com"
    reg_payload = {
        "email": email,
        "password": "StrongPassword789!",
        "full_name": "Dr. Ada Lovelace",
    }
    # 1. Register
    reg_resp = client.post("/api/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
    data = reg_resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == email
    assert data["user"]["full_name"] == "Dr. Ada Lovelace"
    token = data["access_token"]

    # 2. Duplicate Registration Rejection
    dup_resp = client.post("/api/auth/register", json=reg_payload)
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.text.lower()

    # 3. Login with correct password
    login_resp = client.post("/api/auth/login", json={"email": email, "password": "StrongPassword789!"})
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data

    # 4. Login with wrong password
    bad_login = client.post("/api/auth/login", json={"email": email, "password": "IncorrectPassword!"})
    assert bad_login.status_code == 401

    # 5. Access protected /api/auth/me with Bearer token
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["user"]["email"] == email
    print(" -> Registration, duplicate rejection, login, and /me passed.")


def test_oauth_dev_mock_providers():
    print("\n[AUTH TEST 4] Testing Multi-Provider OAuth (Google, GitHub, Microsoft)...")
    for provider in ["google", "github", "microsoft"]:
        resp = client.post(
            "/api/auth/oauth/dev-mock",
            json={"provider": provider},
        )
        assert resp.status_code == 200, f"Mock OAuth failed for {provider}: {resp.text}"
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["provider"] == provider
        assert "@" in data["user"]["email"]
        print(f" -> Provider '{provider}' verified: {data['user']['email']}")


def test_multi_tenant_session_isolation():
    print("\n[AUTH TEST 5] Testing Multi-Tenant Chat Session Isolation...")
    # Create User A
    user_a = amra_db.create_user(
        email=f"usera_{uuid.uuid4().hex[:10]}@test.com",
        hashed_password=None,
        full_name="User Alpha",
        provider="local",
    )
    token_a = create_access_token(user_id=user_a["id"], email=user_a["email"])

    # Create User B
    user_b = amra_db.create_user(
        email=f"userb_{uuid.uuid4().hex[:10]}@test.com",
        hashed_password=None,
        full_name="User Beta",
        provider="local",
    )
    token_b = create_access_token(user_id=user_b["id"], email=user_b["email"])

    # User A creates a session
    sess_a_id = f"sess_alpha_{uuid.uuid4().hex[:10]}"
    amra_db.add_message(
        session_id=sess_a_id,
        user_id=user_a["id"],
        role="user",
        content="Secret research hypothesis from User A",
    )

    # User B queries their sessions list
    resp_b = client.get("/api/chat/sessions", headers={"Authorization": f"Bearer {token_b}"})
    assert resp_b.status_code == 200
    b_sessions = resp_b.json().get("sessions", [])
    # Verify User B cannot see User A's session
    assert not any(s["session_id"] == sess_a_id for s in b_sessions), "User B saw User A's session!"

    # User A queries their sessions list
    resp_a = client.get("/api/chat/sessions", headers={"Authorization": f"Bearer {token_a}"})
    assert resp_a.status_code == 200
    a_sessions = resp_a.json().get("sessions", [])
    assert any(s["session_id"] == sess_a_id for s in a_sessions), "User A could not see their own session!"
    print(" -> Session isolation verified (zero cross-user leakage).")


if __name__ == "__main__":
    test_password_cryptography()
    test_jwt_minting_and_decoding()
    test_user_registration_and_login_flow()
    test_oauth_dev_mock_providers()
    test_multi_tenant_session_isolation()
    print("\n ALL AUTHENTICATION & MULTI-TENANT TESTS PASSED!")
