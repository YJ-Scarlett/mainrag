from typing import Annotated

from fastapi import APIRouter, Depends

from core.security import require_student
from db.models import User
from schemas.reinforcement import (
    ReinforcementCheckRequest,
    ReinforcementGenerateRequest,
)
from services.reinforcement_service import (
    check_reinforcement_answer,
    generate_reinforcement,
)

router = APIRouter()


@router.post("/generate")
async def generate(
    body: ReinforcementGenerateRequest,
    _: Annotated[User, Depends(require_student)],
):
    return await generate_reinforcement(
        body.knowledge_point,
        body.count,
    )


@router.post("/check")
def check(
    body: ReinforcementCheckRequest,
    _: Annotated[User, Depends(require_student)],
):
    return check_reinforcement_answer(
        body.session_id,
        body.question_id,
        body.answer,
    )
