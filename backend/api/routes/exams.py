from fastapi import APIRouter, Header, HTTPException

from schemas.exam import GradeSubmissionRequest, GenerateExamRequest, PublishExamRequest, SubmitExamRequest
from services.exam_service import (
    delete_exam, generate_exam, list_exams, publish_exam,
    grade_submission, list_submissions, student_submission_view, student_submissions, submit_exam, wrong_questions,
)

router = APIRouter()


@router.post("/generate")
async def generate(body: GenerateExamRequest):
    return await generate_exam(body.document_id, body.chapter, body.title, body.count, body.difficulty, body.question_types)


@router.get("")
def get_exams(published_only: bool = False):
    items = list_exams(published_only)
    if published_only:
        items = [
            {**exam, "questions": [{key: value for key, value in question.items() if key not in {"answer", "analysis"}} for question in exam["questions"]]}
            for exam in items
        ]
    return {"items": items}


@router.post("/{exam_id}/publish")
def publish(exam_id: str, body: PublishExamRequest | None = None):
    return publish_exam(exam_id, body.question_ids if body else None)


@router.delete("/{exam_id}")
def remove(exam_id: str):
    delete_exam(exam_id)
    return {"message": "已删除"}


@router.post("/{exam_id}/submit")
async def submit(exam_id: str, body: SubmitExamRequest):
    result = await submit_exam(exam_id, body.student, body.answers, body.solution_grading)
    return student_submission_view(result)


@router.get("/submissions/all")
def all_submissions(status: str | None = None, x_role: str = Header("", alias="X-Role")):
    if x_role != "teacher":
        raise HTTPException(403, "仅教师可以查看学生试卷")
    return {"items": list_submissions(status)}


@router.post("/submissions/{submission_id}/grade")
def teacher_grade(submission_id: str, body: GradeSubmissionRequest, x_role: str = Header("", alias="X-Role")):
    if x_role != "teacher":
        raise HTTPException(403, "仅教师可以批改试卷")
    grades = {question_id: item.model_dump() for question_id, item in body.grades.items()}
    return grade_submission(submission_id, grades, body.overall_comment)


@router.get("/student/submissions")
def submissions(student: str = "张同学"):
    return {"items": student_submissions(student)}


@router.get("/student/wrongbook")
def wrongbook(student: str = "张同学"):
    return {"items": wrong_questions(student)}
