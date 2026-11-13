"""Authentication & Access Control Dependency for AMRA Backend.

Provides:
- PBKDF2-HMAC-SHA256 password hashing & constant-time verification (NIST compliant, zero C-deps)
- PyJWT access token minting and validation
- Multi-provider user resolution (Developer API Key, JWT User Session)
- Multi-tenant current_user dependency for route authorization
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from fastapi import Security, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from .config import settings
from .db.database import amra_db

# Header extractors (auto_error=False to allow fallback between Bearer, X-API-Key, and query token)
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# =============================================================================
# PASSWORD CRYPTOGRAPHY (PBKDF2-HMAC-SHA256)
# =============================================================================

def hash_password(password: str) -> str:
    """Hashes a plaintext password using PBKDF2-HMAC-SHA256 with 100,000 iterations.
    
    Returns a salt-prefixed colon-delimited string: '<salt>:<hex_hash>'.
    """
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return f"{salt}:{key.hex()}"


def verify_password(plain_password: str, hashed_str: Optional[str]) -> bool:
    """Verifies a plain password against a stored PBKDF2 hash using constant-time comparison."""
    if not hashed_str or not plain_password:
        return False
    try:
        # Support both ':' and '$' delimiter
        delimiter = ":" if ":" in hashed_str else "$"
        parts = hashed_str.split(delimiter)
        if len(parts) != 2:
            return False
        salt, expected_hex = parts[0], parts[1]
        test_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        )
        return secrets.compare_digest(test_key.hex(), expected_hex)
    except Exception:
        return False


# =============================================================================
# JWT TOKEN HANDLING
# =============================================================================

def create_access_token(
    user_id: str,
    email: str,
    role: str = "user",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Mints a signed JWT access token for user sessions."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.JWT_EXPIRATION_DAYS)

    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token. Raises HTTPException 401 on invalid/expired token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =============================================================================
# DEPENDENCIES
# =============================================================================

async def get_current_user(
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    header_key: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Query(None, alias="api_key"),
) -> Dict[str, Any]:
    """Resolves and validates the current user identity from Bearer token, header, or query key.
    
    Supports:
    1. System Developer Key (settings.API_AUTH_KEY) -> returns developer admin profile.
    2. User JWT Access Token -> validates and looks up user in database.
    3. Auth disabled mode -> returns developer profile.
    """
    if not settings.AUTH_ENABLED or os.getenv("AMRA_DISABLE_AUTH", "0") == "1":
        return {
            "id": "usr_default_dev",
            "email": "developer@amra.local",
            "full_name": "AMRA Research Developer",
            "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=amra_dev",
            "provider": "system",
            "role": "admin",
        }

    token = None
    if bearer_creds and bearer_creds.credentials:
        token = bearer_creds.credentials.strip()
    elif header_key:
        token = header_key.strip()
    elif query_key:
        token = query_key.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide 'Authorization: Bearer <token>', 'X-API-Key: <key>', or '?api_key=<key>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Check if token matches Developer API key (constant-time comparison)
    if secrets.compare_digest(token, settings.API_AUTH_KEY):
        return {
            "id": "usr_default_dev",
            "email": "developer@amra.local",
            "full_name": "AMRA Research Developer",
            "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=amra_dev",
            "provider": "system",
            "role": "admin",
        }

    # 2. Check if token is a valid JWT session token
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token: missing subject identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = amra_db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Sanitize user dict (remove password hash)
    sanitized = {k: v for k, v in user.items() if k != "hashed_password"}
    sanitized["role"] = payload.get("role", "user")
    return sanitized


async def verify_api_key(
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    header_key: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Query(None, alias="api_key"),
) -> str:
    """Backward-compatible endpoint verifier that authenticates and returns the caller token."""
    user = await get_current_user(bearer_creds, header_key, query_key)
    return user.get("id", "authenticated")
