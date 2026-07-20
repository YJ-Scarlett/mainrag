from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.config import settings
from core.security import create_access_token, get_current_user, require_teacher
from db.database import get_db
from db.models import User
from schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from services.user_service import (
    authenticate_user,
    create_user,
    list_users,
    user_to_public,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse, tags=["认证"])
def login(
    body: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
):
    user = authenticate_user(
        db,
        username=body.username,
        password=body.password,
        role=body.role,
    )
    if not user:
        raise HTTPException(401, "账号、密码或身份选择不正确")

    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": user_to_public(user),
    }


@router.post("/register", tags=["认证"])
def register(
    body: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
):
    if (
        body.role == "teacher"
        and settings.teacher_invite_code
        and body.teacher_invite_code.strip() != settings.teacher_invite_code
    ):
        raise HTTPException(403, "教师邀请码不正确")

    user = create_user(
        db,
        name=body.name,
        password=body.password,
        role=body.role,
    )
    return {
        "message": "注册成功",
        "user": user_to_public(user),
    }


@router.get("/me", response_model=UserPublic, tags=["认证"])
def me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@router.get("/users", tags=["认证"])
def get_users(
    _: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
):
    return {"items": [user_to_public(user) for user in list_users(db)]}
