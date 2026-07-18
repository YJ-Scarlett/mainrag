from fastapi import APIRouter, Header, HTTPException

from schemas.reinforcement import (
    ReinforcementCheckRequest,
    ReinforcementGenerateRequest,
)
from services.reinforcement_service import (
    check_reinforcement_answer,
    generate_reinforcement,
)


router = APIRouter()


def _require_student(x_role: str) -> None:
    if x_role != "student":
        raise HTTPException(
            403,
            "仅学生可以使用专项巩固练习。",
        )


@router.post("/generate")
async def generate(
    body: ReinforcementGenerateRequest,
    x_role: str = Header("", alias="X-Role"),
):
    _require_student(x_role)

    return await generate_reinforcement(
        body.knowledge_point,
        body.count,
    )


@router.post("/check")
def check(
    body: ReinforcementCheckRequest,
    x_role: str = Header("", alias="X-Role"),
):
    _require_student(x_role)

    return check_reinforcement_answer(
        body.session_id,
        body.question_id,
        body.answer,
    )