from fastapi import APIRouter

from services.analysis_service import build_analysis, build_class_analysis

router = APIRouter()


@router.get("/student")
def student_analysis(student: str):
    return build_analysis(student)

@router.get("/class")
def class_analysis():
    return build_class_analysis()
