import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.config import settings
from db.database import SessionLocal
from db.models import ClassStudent, ClassTeacher, Classroom, User
from services.user_service import list_users, migrate_legacy_users
from storage.json_store import store


def _backup_once(source: Path, destination_name: str) -> None:
    if not source.exists():
        return
    destination = settings.backup_dir / destination_name
    if not destination.exists():
        shutil.copy2(source, destination)


def _identity_maps(users: list[User]) -> tuple[dict[str, str], dict[str, dict]]:
    alias_to_id: dict[str, str] = {}
    user_by_id: dict[str, dict] = {}

    for user in users:
        public = {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role,
        }
        user_by_id[user.id] = public
        for alias in {user.id, user.username, user.name}:
            if alias:
                alias_to_id[str(alias)] = user.id

    return alias_to_id, user_by_id


def _resolve_user_id(value: object, alias_to_id: dict[str, str]) -> str | None:
    if value is None:
        return None
    return alias_to_id.get(str(value).strip())


def migrate_store_identity_fields(db: Session) -> dict:
    path = settings.database_file
    if not path.exists():
        data = store.load()
    else:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"业务数据文件读取失败：{path}") from exc

    users = list_users(db)
    alias_to_id, user_by_id = _identity_maps(users)
    default_teacher = next((user for user in users if user.role == "teacher"), None)

    changed = False
    updated_counts = {
        "activities": 0,
        "submissions": 0,
        "questions": 0,
        "chat_history": 0,
        "documents": 0,
        "exams": 0,
    }
    unresolved: list[dict] = []

    for collection_name in ("activities", "submissions"):
        for index, item in enumerate(data.get(collection_name, [])):
            if item.get("student_id"):
                continue
            user_id = _resolve_user_id(item.get("student"), alias_to_id)
            if user_id:
                item["student_id"] = user_id
                item.setdefault("student_name", user_by_id[user_id]["name"])
                changed = True
                updated_counts[collection_name] += 1
            else:
                unresolved.append(
                    {
                        "collection": collection_name,
                        "index": index,
                        "legacy_value": item.get("student"),
                    }
                )

    for collection_name in ("questions", "chat_history"):
        for index, item in enumerate(data.get(collection_name, [])):
            if item.get("user_id"):
                continue
            user_id = _resolve_user_id(item.get("student"), alias_to_id)
            if user_id:
                item["user_id"] = user_id
                item.setdefault("user_name", user_by_id[user_id]["name"])
                changed = True
                updated_counts[collection_name] += 1
            else:
                unresolved.append(
                    {
                        "collection": collection_name,
                        "index": index,
                        "legacy_value": item.get("student"),
                    }
                )

    # 课程资料保持全局共享，只记录上传者用于删除权限，不增加班级字段。
    if default_teacher:
        for item in data.get("documents", []):
            if not item.get("owner_teacher_id"):
                item["owner_teacher_id"] = default_teacher.id
                item.setdefault("owner_teacher_name", default_teacher.name)
                changed = True
                updated_counts["documents"] += 1

        for item in data.get("exams", []):
            if not item.get("creator_teacher_id"):
                item["creator_teacher_id"] = default_teacher.id
                item.setdefault("creator_teacher_name", default_teacher.name)
                changed = True
                updated_counts["exams"] += 1

    if changed:
        _backup_once(path, "store.before_identity_v1.json")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "source": str(path),
        "changed": changed,
        "updated": updated_counts,
        "unresolved": unresolved,
    }


def migrate_default_classroom(db: Session) -> dict:
    """首次升级到班级版本时，为现有演示账号创建一个默认班级。"""

    existing_count = db.scalar(select(func.count()).select_from(Classroom)) or 0
    if existing_count:
        return {
            "created": False,
            "reason": "classes_already_exist",
            "class_count": int(existing_count),
        }

    users = list_users(db)
    teachers = [user for user in users if user.role == "teacher" and user.status == "active"]
    students = [user for user in users if user.role == "student" and user.status == "active"]
    if not teachers:
        return {
            "created": False,
            "reason": "no_active_teacher",
            "class_count": 0,
        }

    owner = teachers[0]
    classroom = Classroom(
        id="cls_default",
        name="默认教学班",
        invite_code="DEFAULT01",
        owner_teacher_id=owner.id,
        status="active",
    )
    db.add(classroom)
    db.flush()

    for teacher in teachers:
        db.add(
            ClassTeacher(
                id=f"ct_default_{teacher.id}",
                class_id=classroom.id,
                teacher_id=teacher.id,
                class_role="owner" if teacher.id == owner.id else "teacher",
                status="active",
            )
        )

    for student in students:
        db.add(
            ClassStudent(
                id=f"cs_default_{student.id}",
                class_id=classroom.id,
                student_id=student.id,
                status="active",
            )
        )

    db.commit()
    return {
        "created": True,
        "class_id": classroom.id,
        "class_name": classroom.name,
        "owner_teacher_id": owner.id,
        "teacher_count": len(teachers),
        "student_count": len(students),
    }


def run_startup_migrations() -> dict:
    with SessionLocal() as db:
        users_report = migrate_legacy_users(db)
        store_report = migrate_store_identity_fields(db)
        classroom_report = migrate_default_classroom(db)

    report = {
        "migration_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "users": users_report,
        "store": store_report,
        "classroom": classroom_report,
    }
    settings.migration_report_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report
