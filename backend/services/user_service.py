import base64
import hashlib
import hmac
import json
import secrets
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import settings
from db.models import User

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return "$".join(
        [
            PASSWORD_SCHEME,
            str(PASSWORD_ITERATIONS),
            _b64encode(salt),
            _b64encode(digest),
        ]
    )


def _legacy_sha256(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def is_legacy_password_hash(value: str) -> bool:
    if len(value) != 64:
        return False
    try:
        int(value, 16)
        return True
    except ValueError:
        return False


def verify_password(password: str, encoded: str) -> bool:
    if is_legacy_password_hash(encoded):
        return hmac.compare_digest(_legacy_sha256(password), encoded)

    try:
        scheme, iterations_text, salt_text, digest_text = encoded.split("$", 3)
        if scheme != PASSWORD_SCHEME:
            return False
        iterations = int(iterations_text)
        salt = _b64decode(salt_text)
        expected = _b64decode(digest_text)
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual, expected)


def user_to_public(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "role": user.role,
        "status": user.status,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.asc())))


def _next_username(db: Session, name: str, role: str) -> str:
    prefix = "s_" if role == "student" else "t_"
    base = f"{prefix}{name.strip()}"
    username = base
    counter = 1
    while get_user_by_username(db, username):
        username = f"{base}{counter}"
        counter += 1
    return username


def create_user(
    db: Session,
    *,
    name: str,
    password: str,
    role: str,
) -> User:
    clean_name = name.strip()
    if not clean_name:
        raise HTTPException(400, "姓名不能为空")
    if role not in {"student", "teacher"}:
        raise HTTPException(400, "角色只能是 student 或 teacher")

    user = User(
        id=f"usr_{uuid.uuid4().hex}",
        username=_next_username(db, clean_name, role),
        name=clean_name,
        role=role,
        password_hash=hash_password(password),
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(
    db: Session,
    *,
    username: str,
    password: str,
    role: str,
) -> User | None:
    user = get_user_by_username(db, username.strip())
    if not user or user.status != "active":
        return None
    if user.role != role:
        return None
    if not verify_password(password, user.password_hash):
        return None

    # 旧 users.json 使用无盐 SHA-256。首次成功登录后自动升级为 PBKDF2。
    if is_legacy_password_hash(user.password_hash):
        user.password_hash = hash_password(password)
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)

    return user


def user_aliases(user: User) -> set[str]:
    return {value for value in {user.id, user.username, user.name} if value}


def _backup_once(source: Path, destination_name: str) -> None:
    if not source.exists():
        return
    destination = settings.backup_dir / destination_name
    if not destination.exists():
        shutil.copy2(source, destination)


def migrate_legacy_users(db: Session) -> dict:
    """把 users.json 中的账号幂等导入 SQLite，不删除原文件。"""

    path = settings.legacy_user_file
    _backup_once(path, "users.before_sqlite.json")

    if not path.exists():
        legacy_users = [
            {
                "username": "teacher",
                "password": _legacy_sha256("123456"),
                "name": "陈老师",
                "role": "teacher",
            },
            {
                "username": "student",
                "password": _legacy_sha256("123456"),
                "name": "张同学",
                "role": "student",
            },
        ]
        path.write_text(
            json.dumps(legacy_users, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    else:
        try:
            legacy_users = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"旧用户文件读取失败：{path}") from exc

    imported = 0
    skipped = 0
    invalid = []

    for index, item in enumerate(legacy_users):
        username = str(item.get("username", "")).strip()
        name = str(item.get("name", "")).strip()
        role = str(item.get("role", "")).strip()
        password_hash = str(item.get("password", "")).strip()

        if not username or not name or role not in {"student", "teacher"} or not password_hash:
            invalid.append({"index": index, "username": username, "reason": "字段不完整"})
            continue

        existing = get_user_by_username(db, username)
        if existing:
            skipped += 1
            continue

        legacy_user_id = f"usr_{uuid.uuid5(uuid.NAMESPACE_URL, f'mainrag:{username}').hex}"
        db.add(
            User(
                id=legacy_user_id,
                username=username,
                name=name,
                role=role,
                password_hash=password_hash,
                status="active",
            )
        )
        imported += 1

    db.commit()
    return {
        "source": str(path),
        "imported": imported,
        "skipped": skipped,
        "invalid": invalid,
        "total_in_sqlite": len(list_users(db)),
    }
