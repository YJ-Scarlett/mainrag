from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from core.config import settings
from db.database import get_db
from db.models import User
from services.user_service import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.access_token_minutes)
    payload = {
        "sub": user.id,
        "username": user.username,
        "role": user.role,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def _credentials_error(detail: str = "登录状态已失效，请重新登录") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _credentials_error("请先登录")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = str(payload.get("sub") or "").strip()
        if not user_id:
            raise _credentials_error()
    except InvalidTokenError as exc:
        raise _credentials_error() from exc

    user = get_user_by_id(db, user_id)
    if not user or user.status != "active":
        raise _credentials_error("账号不存在或已停用")
    return user


def require_teacher(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != "teacher":
        raise HTTPException(403, "仅教师可以执行此操作")
    return current_user


def require_student(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != "student":
        raise HTTPException(403, "仅学生可以执行此操作")
    return current_user
