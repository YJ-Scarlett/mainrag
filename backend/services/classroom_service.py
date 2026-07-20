import secrets
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import ClassJoinRequest, ClassStudent, ClassTeacher, Classroom, User
from services.user_service import get_user_by_id, get_user_by_username


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _user_public(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "role": user.role,
        "status": user.status,
    }


def _generate_invite_code(db: Session) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for _ in range(30):
        code = "".join(secrets.choice(alphabet) for _ in range(8))
        exists = db.scalar(select(Classroom.id).where(Classroom.invite_code == code))
        if not exists:
            return code
    raise HTTPException(500, "班级邀请码生成失败，请重试")


def _get_classroom(db: Session, class_id: str) -> Classroom:
    classroom = db.get(Classroom, class_id)
    if not classroom or classroom.status != "active":
        raise HTTPException(404, "班级不存在或已归档")
    return classroom


def _active_teacher_membership(
    db: Session,
    class_id: str,
    teacher_id: str,
) -> ClassTeacher | None:
    return db.scalar(
        select(ClassTeacher).where(
            ClassTeacher.class_id == class_id,
            ClassTeacher.teacher_id == teacher_id,
            ClassTeacher.status == "active",
        )
    )


def require_class_teacher(
    db: Session,
    class_id: str,
    teacher: User,
) -> tuple[Classroom, ClassTeacher]:
    classroom = _get_classroom(db, class_id)
    membership = _active_teacher_membership(db, class_id, teacher.id)
    if not membership:
        raise HTTPException(403, "你不是该班级教师")
    return classroom, membership


def require_class_owner(
    db: Session,
    class_id: str,
    teacher: User,
) -> Classroom:
    classroom, membership = require_class_teacher(db, class_id, teacher)
    if classroom.owner_teacher_id != teacher.id or membership.class_role != "owner":
        raise HTTPException(403, "仅班级负责人可以执行此操作")
    return classroom


def _class_counts(db: Session, class_id: str) -> tuple[int, int, int]:
    student_count = db.scalar(
        select(func.count()).select_from(ClassStudent).where(
            ClassStudent.class_id == class_id,
            ClassStudent.status == "active",
        )
    ) or 0
    teacher_count = db.scalar(
        select(func.count()).select_from(ClassTeacher).where(
            ClassTeacher.class_id == class_id,
            ClassTeacher.status == "active",
        )
    ) or 0
    pending_count = db.scalar(
        select(func.count()).select_from(ClassJoinRequest).where(
            ClassJoinRequest.class_id == class_id,
            ClassJoinRequest.status == "pending",
        )
    ) or 0
    return int(student_count), int(teacher_count), int(pending_count)


def classroom_to_public(
    db: Session,
    classroom: Classroom,
    *,
    current_teacher_id: str | None = None,
) -> dict:
    student_count, teacher_count, pending_count = _class_counts(db, classroom.id)
    current_role = None
    if current_teacher_id:
        membership = _active_teacher_membership(db, classroom.id, current_teacher_id)
        current_role = membership.class_role if membership else None
    return {
        "id": classroom.id,
        "name": classroom.name,
        "invite_code": classroom.invite_code,
        "owner_teacher_id": classroom.owner_teacher_id,
        "status": classroom.status,
        "created_at": _iso(classroom.created_at),
        "updated_at": _iso(classroom.updated_at),
        "current_teacher_role": current_role,
        "student_count": student_count,
        "teacher_count": teacher_count,
        "pending_request_count": pending_count,
    }


def create_classroom(db: Session, teacher: User, name: str) -> dict:
    clean_name = name.strip()
    if not clean_name:
        raise HTTPException(400, "班级名称不能为空")

    classroom = Classroom(
        id=_new_id("cls"),
        name=clean_name,
        invite_code=_generate_invite_code(db),
        owner_teacher_id=teacher.id,
        status="active",
    )
    db.add(classroom)
    db.flush()
    db.add(
        ClassTeacher(
            id=_new_id("ct"),
            class_id=classroom.id,
            teacher_id=teacher.id,
            class_role="owner",
            status="active",
        )
    )
    db.commit()
    db.refresh(classroom)
    return classroom_to_public(db, classroom, current_teacher_id=teacher.id)


def list_teacher_classrooms(db: Session, teacher: User) -> list[dict]:
    classrooms = list(
        db.scalars(
            select(Classroom)
            .join(ClassTeacher, ClassTeacher.class_id == Classroom.id)
            .where(
                ClassTeacher.teacher_id == teacher.id,
                ClassTeacher.status == "active",
                Classroom.status == "active",
            )
            .order_by(Classroom.created_at.asc())
        )
    )
    return [
        classroom_to_public(db, classroom, current_teacher_id=teacher.id)
        for classroom in classrooms
    ]


def list_class_teachers(db: Session, class_id: str, teacher: User) -> list[dict]:
    require_class_teacher(db, class_id, teacher)
    rows = db.execute(
        select(ClassTeacher, User)
        .join(User, User.id == ClassTeacher.teacher_id)
        .where(
            ClassTeacher.class_id == class_id,
            ClassTeacher.status == "active",
        )
        .order_by(ClassTeacher.class_role.asc(), ClassTeacher.joined_at.asc())
    ).all()
    return [
        {
            **_user_public(user),
            "class_role": membership.class_role,
            "joined_at": _iso(membership.joined_at),
        }
        for membership, user in rows
    ]


def list_class_students(db: Session, class_id: str, teacher: User) -> list[dict]:
    require_class_teacher(db, class_id, teacher)
    rows = db.execute(
        select(ClassStudent, User)
        .join(User, User.id == ClassStudent.student_id)
        .where(
            ClassStudent.class_id == class_id,
            ClassStudent.status == "active",
        )
        .order_by(ClassStudent.joined_at.asc())
    ).all()
    return [
        {
            **_user_public(user),
            "joined_at": _iso(membership.joined_at),
        }
        for membership, user in rows
    ]


def get_classroom_detail(db: Session, class_id: str, teacher: User) -> dict:
    classroom, _ = require_class_teacher(db, class_id, teacher)
    return {
        "classroom": classroom_to_public(
            db,
            classroom,
            current_teacher_id=teacher.id,
        ),
        "teachers": list_class_teachers(db, class_id, teacher),
        "students": list_class_students(db, class_id, teacher),
    }


def add_teacher_to_class(
    db: Session,
    class_id: str,
    owner: User,
    username: str,
) -> dict:
    require_class_owner(db, class_id, owner)
    target = get_user_by_username(db, username.strip())
    if not target or target.status != "active" or target.role != "teacher":
        raise HTTPException(404, "未找到可用的教师账号")

    membership = db.scalar(
        select(ClassTeacher).where(
            ClassTeacher.class_id == class_id,
            ClassTeacher.teacher_id == target.id,
        )
    )
    if membership and membership.status == "active":
        raise HTTPException(400, "该教师已经在班级中")
    if membership:
        membership.status = "active"
        membership.class_role = "teacher"
        membership.joined_at = _utc_now()
    else:
        membership = ClassTeacher(
            id=_new_id("ct"),
            class_id=class_id,
            teacher_id=target.id,
            class_role="teacher",
            status="active",
        )
        db.add(membership)
    db.commit()
    return {
        **_user_public(target),
        "class_role": membership.class_role,
        "joined_at": _iso(membership.joined_at),
    }


def remove_teacher_from_class(
    db: Session,
    class_id: str,
    owner: User,
    teacher_id: str,
) -> None:
    classroom = require_class_owner(db, class_id, owner)
    if teacher_id == classroom.owner_teacher_id:
        raise HTTPException(400, "班级负责人不能被移除")
    membership = _active_teacher_membership(db, class_id, teacher_id)
    if not membership:
        raise HTTPException(404, "该教师不在班级中")
    membership.status = "inactive"
    db.commit()


def _active_student_membership(db: Session, student_id: str) -> ClassStudent | None:
    return db.scalar(
        select(ClassStudent).where(
            ClassStudent.student_id == student_id,
            ClassStudent.status == "active",
        )
    )


def _assign_student(db: Session, class_id: str, student: User) -> ClassStudent:
    active = _active_student_membership(db, student.id)
    if active:
        if active.class_id == class_id:
            raise HTTPException(400, "该学生已经在本班")
        raise HTTPException(409, "该学生已属于其他班级")

    membership = db.scalar(
        select(ClassStudent).where(ClassStudent.student_id == student.id)
    )
    if membership:
        membership.class_id = class_id
        membership.status = "active"
        membership.joined_at = _utc_now()
        membership.left_at = None
    else:
        membership = ClassStudent(
            id=_new_id("cs"),
            class_id=class_id,
            student_id=student.id,
            status="active",
        )
        db.add(membership)
    return membership


def add_student_to_class(
    db: Session,
    class_id: str,
    teacher: User,
    username: str,
) -> dict:
    require_class_teacher(db, class_id, teacher)
    student = get_user_by_username(db, username.strip())
    if not student or student.status != "active" or student.role != "student":
        raise HTTPException(404, "未找到可用的学生账号")
    membership = _assign_student(db, class_id, student)
    db.commit()
    return {
        **_user_public(student),
        "joined_at": _iso(membership.joined_at),
    }


def remove_student_from_class(
    db: Session,
    class_id: str,
    teacher: User,
    student_id: str,
) -> None:
    require_class_teacher(db, class_id, teacher)
    membership = db.scalar(
        select(ClassStudent).where(
            ClassStudent.student_id == student_id,
            ClassStudent.class_id == class_id,
            ClassStudent.status == "active",
        )
    )
    if not membership:
        raise HTTPException(404, "该学生不在本班")
    membership.status = "inactive"
    membership.left_at = _utc_now()
    db.commit()


def get_student_classroom(db: Session, student: User) -> dict | None:
    row = db.execute(
        select(ClassStudent, Classroom)
        .join(Classroom, Classroom.id == ClassStudent.class_id)
        .where(
            ClassStudent.student_id == student.id,
            ClassStudent.status == "active",
            Classroom.status == "active",
        )
    ).first()
    if not row:
        return None
    membership, classroom = row
    teacher_rows = db.execute(
        select(ClassTeacher, User)
        .join(User, User.id == ClassTeacher.teacher_id)
        .where(
            ClassTeacher.class_id == classroom.id,
            ClassTeacher.status == "active",
        )
        .order_by(ClassTeacher.class_role.asc(), ClassTeacher.joined_at.asc())
    ).all()
    return {
        "classroom": {
            **classroom_to_public(db, classroom),
            "joined_at": _iso(membership.joined_at),
        },
        "teachers": [
            {
                **_user_public(user),
                "class_role": teacher_membership.class_role,
            }
            for teacher_membership, user in teacher_rows
        ],
    }


def apply_to_join_class(db: Session, student: User, invite_code: str) -> dict:
    if _active_student_membership(db, student.id):
        raise HTTPException(409, "你已经加入班级，不能重复申请")

    code = invite_code.strip().upper()
    classroom = db.scalar(
        select(Classroom).where(
            Classroom.invite_code == code,
            Classroom.status == "active",
        )
    )
    if not classroom:
        raise HTTPException(404, "班级邀请码不存在")

    pending = db.scalar(
        select(ClassJoinRequest).where(
            ClassJoinRequest.student_id == student.id,
            ClassJoinRequest.status == "pending",
        )
    )
    if pending:
        if pending.class_id == classroom.id:
            raise HTTPException(400, "你已经提交过该班级申请")
        raise HTTPException(409, "你已有待审核的班级申请，请先取消")

    item = ClassJoinRequest(
        id=_new_id("cjr"),
        class_id=classroom.id,
        student_id=student.id,
        status="pending",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "class_id": classroom.id,
        "class_name": classroom.name,
        "status": item.status,
        "created_at": _iso(item.created_at),
    }


def list_student_join_requests(db: Session, student: User) -> list[dict]:
    rows = db.execute(
        select(ClassJoinRequest, Classroom)
        .join(Classroom, Classroom.id == ClassJoinRequest.class_id)
        .where(ClassJoinRequest.student_id == student.id)
        .order_by(ClassJoinRequest.created_at.desc())
    ).all()
    return [
        {
            "id": item.id,
            "class_id": classroom.id,
            "class_name": classroom.name,
            "status": item.status,
            "created_at": _iso(item.created_at),
            "reviewed_at": _iso(item.reviewed_at),
            "review_note": item.review_note,
        }
        for item, classroom in rows
    ]


def cancel_student_join_request(
    db: Session,
    student: User,
    request_id: str,
) -> None:
    item = db.get(ClassJoinRequest, request_id)
    if not item or item.student_id != student.id:
        raise HTTPException(404, "申请不存在")
    if item.status != "pending":
        raise HTTPException(400, "该申请已处理，不能取消")
    item.status = "cancelled"
    item.reviewed_at = _utc_now()
    db.commit()


def list_class_join_requests(
    db: Session,
    class_id: str,
    teacher: User,
    status: str | None = None,
) -> list[dict]:
    require_class_teacher(db, class_id, teacher)
    statement = (
        select(ClassJoinRequest, User)
        .join(User, User.id == ClassJoinRequest.student_id)
        .where(ClassJoinRequest.class_id == class_id)
    )
    if status:
        statement = statement.where(ClassJoinRequest.status == status)
    rows = db.execute(statement.order_by(ClassJoinRequest.created_at.desc())).all()
    return [
        {
            "id": item.id,
            "class_id": item.class_id,
            "student": _user_public(student),
            "status": item.status,
            "created_at": _iso(item.created_at),
            "reviewed_at": _iso(item.reviewed_at),
            "reviewed_by": item.reviewed_by,
            "review_note": item.review_note,
        }
        for item, student in rows
    ]


def review_join_request(
    db: Session,
    class_id: str,
    request_id: str,
    teacher: User,
    *,
    approve: bool,
    note: str = "",
) -> dict:
    require_class_teacher(db, class_id, teacher)
    item = db.get(ClassJoinRequest, request_id)
    if not item or item.class_id != class_id:
        raise HTTPException(404, "申请不存在")
    if item.status != "pending":
        raise HTTPException(400, "该申请已经处理")

    student = get_user_by_id(db, item.student_id)
    if not student or student.status != "active" or student.role != "student":
        raise HTTPException(404, "申请学生账号不存在或不可用")

    if approve:
        membership = _assign_student(db, class_id, student)
        item.status = "approved"
        # 审核通过后，自动关闭该学生其他待审核申请。
        other_pending = list(
            db.scalars(
                select(ClassJoinRequest).where(
                    ClassJoinRequest.student_id == student.id,
                    ClassJoinRequest.id != item.id,
                    ClassJoinRequest.status == "pending",
                )
            )
        )
        for other in other_pending:
            other.status = "rejected"
            other.reviewed_at = _utc_now()
            other.reviewed_by = teacher.id
            other.review_note = "学生已加入其他班级"
    else:
        membership = None
        item.status = "rejected"

    item.reviewed_at = _utc_now()
    item.reviewed_by = teacher.id
    item.review_note = note.strip()
    db.commit()
    return {
        "request_id": item.id,
        "status": item.status,
        "student": _user_public(student),
        "membership_id": membership.id if membership else None,
    }
