from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.security import require_student, require_teacher
from db.database import get_db
from db.models import User
from services.analysis_service import (
    build_class_analysis,
    build_user_analysis,
)

router = APIRouter()


@router.get("/student")
def student_analysis(
    current_user: Annotated[
        User,
        Depends(require_student),
    ],
):
    return build_user_analysis(current_user)


@router.get("/class")
def class_analysis(
    current_user: Annotated[
        User,
        Depends(require_teacher),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    class_id: str | None = None,
):
    return build_class_analysis(
        db,
        current_user,
        class_id=class_id,
    )