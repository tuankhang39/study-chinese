from datetime import date, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def xp_to_level(xp: int) -> int:
    return max(1, xp // 200 + 1)


def award_xp(db: Session, user: User, amount: int, reason: str) -> User:
    from app.models import XpEvent

    user.xp += amount
    user.level = xp_to_level(user.xp)
    db.add(XpEvent(user_id=user.id, amount=amount, reason=reason))
    return user


def touch_streak(user: User, today: date | None = None) -> None:
    today = today or date.today()
    if user.last_active_date == today:
        return
    if user.last_active_date == today - timedelta(days=1):
        user.streak += 1
    else:
        user.streak = 1
    user.last_active_date = today


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]
