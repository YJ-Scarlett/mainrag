from typing import Annotated

from fastapi import APIRouter, Depends

from core.security import require_student, require_teacher
from db.models import User
from services.analysis_service import build_class_analysis, build_user_analysis

router = APIRouter()


@router.get("/student")
def student_analysis(
    current_user: Annotated[User, Depends(require_student)],
):
    return build_user_analysis(current_user)


@router.get("/class")
def class_analysis(
    _: Annotated[User, Depends(require_teacher)],
):
    return build_class_analysis()
