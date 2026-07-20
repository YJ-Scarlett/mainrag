from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from core.security import get_current_user, require_student, require_teacher
from db.models import User
from schemas.exam import (
    GradeSubmissionRequest,
    GenerateExamRequest,
    PublishExamRequest,
    SubmitExamRequest,
)
from services.exam_service import (
    delete_exam,
    generate_exam,
    grade_submission,
    list_exams,
    list_submissions,
    publish_exam,
    student_submission_view,
    student_submissions,
    submit_exam,
    wrong_questions,
)
from services.identity_service import user_aliases

router = APIRouter()


@router.post("/generate")
async def generate(
    body: GenerateExamRequest,
    current_user: Annotated[User, Depends(require_teacher)],
):
    return await generate_exam(
        body.document_id,
        body.chapter,
        body.title,
        body.count,
        body.difficulty,
        body.question_types,
        creator_teacher_id=current_user.id,
        creator_teacher_name=current_user.name,
    )


@router.get("")
def get_exams(
    current_user: Annotated[User, Depends(get_current_user)],
    published_only: bool = False,
):
    if not published_only and current_user.role != "teacher":
        raise HTTPException(403, "仅教师可以查看未发布习题")

    items = list_exams(
        published_only,
        creator_teacher_id=(current_user.id if not published_only else None),
    )
    if published_only:
        items = [
            {
                **exam,
                "questions": [
                    {
                        key: value
                        for key, value in question.items()
                        if key not in {"answer", "analysis"}
                    }
                    for question in exam["questions"]
                ],
            }
            for exam in items
        ]
    return {"items": items}


@router.post("/{exam_id}/publish")
def publish(
    exam_id: str,
    current_user: Annotated[User, Depends(require_teacher)],
    body: PublishExamRequest | None = None,
):
    return publish_exam(
        exam_id,
        current_user.id,
        body.question_ids if body else None,
    )


@router.delete("/{exam_id}")
def remove(
    exam_id: str,
    current_user: Annotated[User, Depends(require_teacher)],
):
    delete_exam(exam_id, current_user.id)
    return {"message": "已删除"}


@router.post("/{exam_id}/submit")
async def submit(
    exam_id: str,
    body: SubmitExamRequest,
    current_user: Annotated[User, Depends(require_student)],
):
    result = await submit_exam(
        exam_id,
        student_id=current_user.id,
        student_username=current_user.username,
        student_name=current_user.name,
        answers=body.answers,
        solution_grading=body.solution_grading,
    )
    return student_submission_view(result)


@router.get("/submissions/all")
def all_submissions(
    current_user: Annotated[User, Depends(require_teacher)],
    status: str | None = None,
):
    return {
        "items": list_submissions(
            status,
            teacher_id=current_user.id,
        )
    }


@router.post("/submissions/{submission_id}/grade")
def teacher_grade(
    submission_id: str,
    body: GradeSubmissionRequest,
    current_user: Annotated[User, Depends(require_teacher)],
):
    grades = {
        question_id: item.model_dump()
        for question_id, item in body.grades.items()
    }
    return grade_submission(
        submission_id,
        grades,
        body.overall_comment,
        teacher_id=current_user.id,
    )


@router.get("/student/submissions")
def submissions(
    current_user: Annotated[User, Depends(require_student)],
):
    return {
        "items": student_submissions(
            student_id=current_user.id,
            aliases=user_aliases(current_user),
        )
    }


@router.get("/student/wrongbook")
def wrongbook(
    current_user: Annotated[User, Depends(require_student)],
):
    return {
        "items": wrong_questions(
            student_id=current_user.id,
            aliases=user_aliases(current_user),
        )
    }
