from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.deps import CurrentUser, DbSession, touch_streak
from app.models import User
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services.fsrs_service import ensure_cards_for_user, get_or_create_mission

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: DbSession) -> TokenResponse:
    existing = db.query(User).filter(User.email == body.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        display_name=body.display_name.strip(),
        role="user",
        plan="free",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    ensure_cards_for_user(db, user.id, limit=80)
    get_or_create_mission(db, user.id)
    touch_streak(user)
    db.commit()
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DbSession) -> TokenResponse:
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    touch_streak(user)
    db.commit()
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> User:
    return user


@router.get("/google/status")
def google_status() -> dict:
    return {"enabled": settings.google_enabled}


@router.get("/google/start")
def google_start() -> RedirectResponse:
    if not settings.google_enabled:
        raise HTTPException(
            status_code=503,
            detail="Google login chưa cấu hình (GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET)",
        )
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/google/callback")
async def google_callback(db: DbSession, code: str | None = None, error: str | None = None):
    web = settings.web_app_url.rstrip("/")
    if error or not code:
        return RedirectResponse(f"{web}/login?error=google_denied")
    if not settings.google_enabled:
        return RedirectResponse(f"{web}/login?error=google_disabled")

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            token_res = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_res.raise_for_status()
            access = token_res.json().get("access_token")
            if not access:
                raise RuntimeError("No access_token from Google")
            info_res = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access}"},
            )
            info_res.raise_for_status()
            info = info_res.json()
    except Exception:
        return RedirectResponse(f"{web}/login?error=google_token")

    sub = info.get("sub")
    email = (info.get("email") or "").lower()
    name = (info.get("name") or email.split("@")[0] or "Học viên").strip()
    if not sub or not email:
        return RedirectResponse(f"{web}/login?error=google_profile")

    user = db.query(User).filter(User.google_sub == sub).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_sub = sub
        else:
            user = User(
                email=email,
                password_hash=None,
                display_name=name[:120],
                google_sub=sub,
                role="user",
                plan="free",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            ensure_cards_for_user(db, user.id, limit=80)
            get_or_create_mission(db, user.id)

    touch_streak(user)
    db.commit()
    token = create_access_token(str(user.id))
    return RedirectResponse(f"{web}/login?token={token}")
