from fastapi import APIRouter

from schemas.exam import GenerateExamRequest, SubmitExamRequest
from services.exam_service import (
    delete_exam, generate_exam, list_exams, publish_exam,
    student_submissions, submit_exam, wrong_questions,
)

router = APIRouter()


@router.post("/generate")
async def generate(body: GenerateExamRequest):
    return await generate_exam(body.document_id, body.chapter, body.title, body.count, body.difficulty)


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
def publish(exam_id: str):
    return publish_exam(exam_id)


@router.delete("/{exam_id}")
def remove(exam_id: str):
    delete_exam(exam_id)
    return {"message": "已删除"}


@router.post("/{exam_id}/submit")
def submit(exam_id: str, body: SubmitExamRequest):
    return submit_exam(exam_id, body.student, body.answers)


@router.get("/student/submissions")
def submissions(student: str = "张同学"):
    return {"items": student_submissions(student)}


@router.get("/student/wrongbook")
def wrongbook(student: str = "张同学"):
    return {"items": wrong_questions(student)}
