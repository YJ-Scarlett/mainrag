from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.security import require_student, require_teacher
from db.database import get_db
from db.models import User
from schemas.classroom import (
    ClassroomCreateRequest,
    ClassroomJoinApplyRequest,
    ClassroomJoinReviewRequest,
    ClassroomStudentAddRequest,
    ClassroomTeacherAddRequest,
)
from services.classroom_service import (
    add_student_to_class,
    add_teacher_to_class,
    apply_to_join_class,
    cancel_student_join_request,
    create_classroom,
    get_classroom_detail,
    get_student_classroom,
    list_class_join_requests,
    list_class_students,
    list_class_teachers,
    list_student_join_requests,
    list_teacher_classrooms,
    remove_student_from_class,
    remove_teacher_from_class,
    review_join_request,
)

router = APIRouter()


# 学生端静态路径必须放在 /{class_id} 之前，避免被动态路径吞掉。
@router.get("/student/me")
def student_classroom(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
):
    return {"item": get_student_classroom(db, current_user)}


@router.post("/student/join-requests")
def student_apply(
    body: ClassroomJoinApplyRequest,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
):
    return {
        "message": "加入申请已提交",
        "item": apply_to_join_class(db, current_user, body.invite_code),
    }


@router.get("/student/join-requests")
def student_requests(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
):
    return {"items": list_student_join_requests(db, current_user)}


@router.delete("/student/join-requests/{request_id}")
def student_cancel_request(
    request_id: str,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
):
    cancel_student_join_request(db, current_user, request_id)
    return {"message": "申请已取消"}


@router.get("")
def teacher_classrooms(
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
):
    return {"items": list_teacher_classrooms(db, current_user)}


@router.post("")
def teacher_create_classroom(
    body: ClassroomCreateRequest,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
):
    return {
        "message": "班级创建成功",
        "item": create_classroom(db, current_user, body.name),
    }


@router.get("/{class_id}")
def teacher_classroom_detail(
    class_id: str,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
):
    return get_classroom_detail(db, class_id, current_user)


@router.get("/{class_id}/students")
def teacher_class_students(
    class_id: str,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
):
    return {"items": list_class_students(db, class_id, current_user)}


@router.post("/{class_id}/students")
def teacher_add_student(
    class_id: str,
    body: ClassroomStudentAddRequest,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
):
    return {
        "message": "学生已加入班级",
        "item": add_student_to_class(
            db,
            class_id,
            current_user,
            body.username,
        ),
    }


@router.delete("/{class_id}/students/{student_id}")
def teacher_remove_student(
    class_id: str,
    student_id: str,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
):
    remove_student_from_class(db, class_id, current_user, student_id)
    return {"message": "学生已移出班级"}


@router.get("/{class_id}/teachers")
def teacher_class_teachers(
    class_id: str,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
):
    return {"items": list_class_teachers(db, class_id, current_user)}


@router.post("/{class_id}/teachers")
def owner_add_teacher(
    class_id: str,
    body: ClassroomTeacherAddRequest,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
):
    return {
        "message": "教师已加入班级",
        "item": add_teacher_to_class(
            db,
            class_id,
            current_user,
            body.username,
        ),
    }


@router.delete("/{class_id}/teachers/{teacher_id}")
def owner_remove_teacher(
    class_id: str,
    teacher_id: str,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
):
    remove_teacher_from_class(db, class_id, current_user, teacher_id)
    return {"message": "教师已移出班级"}


@router.get("/{class_id}/join-requests")
def teacher_join_requests(
    class_id: str,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
    status: str | None = None,
):
    return {
        "items": list_class_join_requests(
            db,
            class_id,
            current_user,
            status,
        )
    }


@router.post("/{class_id}/join-requests/{request_id}/approve")
def teacher_approve_request(
    class_id: str,
    request_id: str,
    body: ClassroomJoinReviewRequest,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
):
    return {
        "message": "申请已通过",
        "item": review_join_request(
            db,
            class_id,
            request_id,
            current_user,
            approve=True,
            note=body.note,
        ),
    }


@router.post("/{class_id}/join-requests/{request_id}/reject")
def teacher_reject_request(
    class_id: str,
    request_id: str,
    body: ClassroomJoinReviewRequest,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
):
    return {
        "message": "申请已拒绝",
        "item": review_join_request(
            db,
            class_id,
            request_id,
            current_user,
            approve=False,
            note=body.note,
        ),
    }
