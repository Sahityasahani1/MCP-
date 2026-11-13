"""Authentication and User Profile Router for AMRA Backend.

Provides:
- POST /api/auth/register: Local email/password registration with validation
- POST /api/auth/login: Local email/password login returning JWT
- GET  /api/auth/me: Returns current authenticated user profile
- GET  /api/auth/oauth/{provider}: Initiates Google, GitHub, or Microsoft OAuth flow
- GET  /api/auth/oauth/callback/{provider}: Handles OAuth authorization code exchange
- POST /api/auth/oauth/dev-mock: Instant 1-click sandbox social sign-in (works out of the box)
"""

import os
import secrets
import urllib.parse
from typing import Dict, Any, Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field

from ..config import settings
from ..db.database import amra_db
from ..auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid user email address")
    password: str = Field(..., min_length=8, description="Password (at least 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=100, description="User full display name")


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered user email address")
    password: str = Field(..., description="Account password")


class DevOAuthMockRequest(BaseModel):
    provider: str = Field(..., description="Provider name: google, github, or microsoft")
    email: Optional[EmailStr] = Field(None, description="Optional custom email")
    full_name: Optional[str] = Field(None, description="Optional display name")


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    provider: str
    role: Optional[str] = "user"
    created_at: float
    last_login: float


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# =============================================================================
# LOCAL REGISTRATION & LOGIN
# =============================================================================

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_user(req: UserRegisterRequest):
    """Registers a new user account with email and password."""
    existing = amra_db.get_user_by_email(req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in.",
        )

    hashed = hash_password(req.password)
    user = amra_db.create_user(
        email=req.email,
        hashed_password=hashed,
        full_name=req.full_name,
        provider="local",
    )

    token = create_access_token(user_id=user["id"], email=user["email"], role="user")
    user_data = {k: v for k, v in user.items() if k != "hashed_password"}
    user_data["role"] = "user"
    return AuthResponse(access_token=token, user=UserResponse(**user_data))


@router.post("/login", response_model=AuthResponse)
async def login_user(req: UserLoginRequest):
    """Authenticates an existing user and returns a signed JWT access token."""
    user = amra_db.get_user_by_email(req.email)
    if not user or not user.get("hashed_password"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    amra_db.update_last_login(user["id"])
    token = create_access_token(user_id=user["id"], email=user["email"], role="user")
    user_data = {k: v for k, v in user.items() if k != "hashed_password"}
    user_data["role"] = "user"
    return AuthResponse(access_token=token, user=UserResponse(**user_data))


@router.get("/me")
async def get_current_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """Returns the authenticated user's profile and session metadata."""
    return {"user": user}


# =============================================================================
# MULTI-PROVIDER OAUTH 2.0 (Google, GitHub, Microsoft)
# =============================================================================

OAUTH_CONFIG = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
        "scopes": "openid email profile",
    },
    "github": {
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scopes": "read:user user:email",
    },
    "microsoft": {
        "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "scopes": "openid email profile User.Read",
    },
}
# Normalize aliases
OAUTH_CONFIG["outlook"] = OAUTH_CONFIG["microsoft"]
OAUTH_CONFIG["gmail"] = OAUTH_CONFIG["google"]


def _get_provider_keys(provider: str):
    p = provider.lower()
    if p in ("google", "gmail"):
        return settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET
    elif p == "github":
        return settings.GITHUB_CLIENT_ID, settings.GITHUB_CLIENT_SECRET
    elif p in ("microsoft", "outlook"):
        return settings.MICROSOFT_CLIENT_ID, settings.MICROSOFT_CLIENT_SECRET
    return "", ""


# =============================================================================
# INSTANT ZERO-FRICTION DEV MOCK OAUTH (Must precede /oauth/{provider} route)
# =============================================================================

@router.get("/oauth/dev-callback")
async def oauth_dev_callback(provider: str = Query("google"), redirect_to: Optional[str] = None):
    """Zero-friction local dev callback that auto-signs in a realistic profile for the chosen provider."""
    provider_key = provider.lower()
    mock_profiles = {
        "google": {
            "name": "Google Researcher",
            "email": "researcher@gmail.com",
            "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=google_user_amra",
            "pid": "goog_sub_9921448",
        },
        "gmail": {
            "name": "Google Researcher",
            "email": "researcher@gmail.com",
            "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=google_user_amra",
            "pid": "goog_sub_9921448",
        },
        "github": {
            "name": "Octocat ML Engineer",
            "email": "engineer@github.com",
            "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=github_user_amra",
            "pid": "gh_sub_1029384",
        },
        "microsoft": {
            "name": "Outlook Enterprise Scientist",
            "email": "scientist@outlook.com",
            "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=ms_user_amra",
            "pid": "ms_sub_8837192",
        },
        "outlook": {
            "name": "Outlook Enterprise Scientist",
            "email": "scientist@outlook.com",
            "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=ms_user_amra",
            "pid": "ms_sub_8837192",
        },
    }
    profile = mock_profiles.get(provider_key, mock_profiles["google"])
    user = amra_db.upsert_oauth_user(
        email=profile["email"],
        full_name=profile["name"],
        avatar_url=profile["avatar"],
        provider=provider_key,
        provider_id=profile["pid"],
    )
    token = create_access_token(user_id=user["id"], email=user["email"], role="user")
    base_target = redirect_to or f"{settings.APP_BASE_URL}/login"
    separator = "&" if "?" in base_target else "?"
    return RedirectResponse(url=f"{base_target}{separator}token={token}")


@router.get("/oauth/{provider}")
async def initiate_oauth(provider: str, redirect_to: Optional[str] = None):
    """Initiates OAuth 2.0 authorization code flow.
    
    If client credentials are configured, redirects to the provider's official OAuth consent screen.
    If client credentials are not configured, redirects smoothly to the developer mock callback.
    """
    provider_key = provider.lower()
    if provider_key == "dev-callback":
        return await oauth_dev_callback(provider="google", redirect_to=redirect_to)

    if provider_key not in OAUTH_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")

    client_id, _ = _get_provider_keys(provider_key)
    callback_url = f"http://127.0.0.1:8000/api/auth/oauth/callback/{provider_key}"

    # If live OAuth client ID is missing, fall back to instant dev mock flow
    if not client_id:
        target_redirect = redirect_to or f"{settings.APP_BASE_URL}/login"
        return RedirectResponse(
            url=f"/api/auth/oauth/dev-callback?provider={provider_key}&redirect_to={urllib.parse.quote(target_redirect)}"
        )

    # Build real OAuth authorization URL
    conf = OAUTH_CONFIG[provider_key]
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": client_id,
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": conf["scopes"],
        "state": state,
    }
    if provider_key in ("google", "gmail"):
        params["access_type"] = "offline"
        params["prompt"] = "select_account"

    auth_url = f"{conf['auth_url']}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/oauth/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
):
    """Handles OAuth code exchange with Google, GitHub, or Microsoft, and mints session JWT."""
    provider_key = provider.lower()
    if error:
        return RedirectResponse(url=f"{settings.APP_BASE_URL}/login?error={urllib.parse.quote(error)}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code from provider.")

    client_id, client_secret = _get_provider_keys(provider_key)
    conf = OAUTH_CONFIG.get(provider_key)
    if not conf or not client_id or not client_secret:
        raise HTTPException(status_code=500, detail=f"OAuth provider '{provider_key}' is not configured on server.")

    callback_url = f"http://127.0.0.1:8000/api/auth/oauth/callback/{provider_key}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Exchange authorization code for token
        if provider_key == "github":
            token_resp = await client.post(
                conf["token_url"],
                headers={"Accept": "application/json"},
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": callback_url,
                },
            )
        else:
            token_resp = await client.post(
                conf["token_url"],
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": callback_url,
                },
            )

        if token_resp.status_code != 200:
            return RedirectResponse(
                url=f"{settings.APP_BASE_URL}/login?error=oauth_token_exchange_failed"
            )

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return RedirectResponse(url=f"{settings.APP_BASE_URL}/login?error=no_access_token")

        # 2. Fetch User Profile
        headers = {"Authorization": f"Bearer {access_token}"}
        user_resp = await client.get(conf["userinfo_url"], headers=headers)
        if user_resp.status_code != 200:
            return RedirectResponse(url=f"{settings.APP_BASE_URL}/login?error=profile_fetch_failed")

        profile = user_resp.json()

        # Normalize profile across providers
        if provider_key in ("google", "gmail"):
            email = profile.get("email")
            full_name = profile.get("name") or email.split("@")[0]
            avatar_url = profile.get("picture")
            provider_id = profile.get("sub")
        elif provider_key == "github":
            provider_id = str(profile.get("id"))
            full_name = profile.get("name") or profile.get("login", "GitHub Researcher")
            avatar_url = profile.get("avatar_url")
            email = profile.get("email")
            # If primary email is private in GitHub profile, fetch from emails endpoint
            if not email:
                emails_resp = await client.get("https://api.github.com/user/emails", headers=headers)
                if emails_resp.status_code == 200:
                    emails = emails_resp.json()
                    primary = next((e["email"] for e in emails if e.get("primary")), None)
                    email = primary or (emails[0]["email"] if emails else f"{profile.get('login')}@users.noreply.github.com")
        elif provider_key in ("microsoft", "outlook"):
            provider_id = profile.get("id")
            email = profile.get("mail") or profile.get("userPrincipalName")
            full_name = profile.get("displayName") or (email.split("@")[0] if email else "Outlook Researcher")
            avatar_url = f"https://api.dicebear.com/7.x/identicon/svg?seed={email or provider_id}"

        if not email:
            email = f"{provider_key}_{provider_id}@amra.local"

    # 3. Upsert user in database
    db_user = amra_db.upsert_oauth_user(
        email=email,
        full_name=full_name,
        avatar_url=avatar_url,
        provider=provider_key,
        provider_id=str(provider_id),
    )

    # 4. Mint AMRA JWT and redirect back to frontend
    amra_jwt = create_access_token(user_id=db_user["id"], email=db_user["email"], role="user")
    return RedirectResponse(url=f"{settings.APP_BASE_URL}/login?token={amra_jwt}")


# =============================================================================
# INSTANT ZERO-FRICTION DEV MOCK OAUTH POST
# =============================================================================

@router.post("/oauth/dev-mock", response_model=AuthResponse)
async def dev_mock_social_login(req: DevOAuthMockRequest):
    """Instant 1-click social sign-in for Next.js frontend and automated tests."""
    provider_key = req.provider.lower()
    if provider_key not in ("google", "gmail", "github", "microsoft", "outlook"):
        raise HTTPException(status_code=400, detail=f"Unsupported mock provider: {req.provider}")

    defaults = {
        "google": ("researcher@gmail.com", "Google Researcher", "https://api.dicebear.com/7.x/bottts/svg?seed=google_user_amra", "goog_mock_001"),
        "gmail": ("researcher@gmail.com", "Google Researcher", "https://api.dicebear.com/7.x/bottts/svg?seed=google_user_amra", "goog_mock_001"),
        "github": ("engineer@github.com", "GitHub Contributor", "https://api.dicebear.com/7.x/bottts/svg?seed=github_user_amra", "gh_mock_002"),
        "microsoft": ("scientist@outlook.com", "Outlook Scientist", "https://api.dicebear.com/7.x/bottts/svg?seed=ms_user_amra", "ms_mock_003"),
        "outlook": ("scientist@outlook.com", "Outlook Scientist", "https://api.dicebear.com/7.x/bottts/svg?seed=ms_user_amra", "ms_mock_003"),
    }

    default_email, default_name, avatar, pid = defaults[provider_key]
    email = str(req.email) if req.email else default_email
    full_name = req.full_name or default_name

    user = amra_db.upsert_oauth_user(
        email=email,
        full_name=full_name,
        avatar_url=avatar,
        provider=provider_key,
        provider_id=pid,
    )

    token = create_access_token(user_id=user["id"], email=user["email"], role="user")
    user_data = {k: v for k, v in user.items() if k != "hashed_password"}
    user_data["role"] = "user"
    return AuthResponse(access_token=token, user=UserResponse(**user_data))
