from pydantic import BaseModel, Field


class GenerateExamRequest(BaseModel):
    document_id: str
    chapter: str = "全文"
    title: str = ""
    count: int = Field(default=5, ge=1, le=20)
    difficulty: str = "中等"
    question_types: list[str] = Field(default_factory=lambda: ["choice", "fill", "solution"])


class PublishExamRequest(BaseModel):
    question_ids: list[str] = Field(default_factory=list)


class SubmitExamRequest(BaseModel):
    # student 字段仅为旧前端兼容；后端始终使用 JWT 中的当前学生。
    student: str | None = None
    answers: dict[str, str]
    solution_grading: str = "ai"


class TeacherGradeItem(BaseModel):
    score: float = Field(ge=0)
    comment: str = ""


class GradeSubmissionRequest(BaseModel):
    grades: dict[str, TeacherGradeItem]
    overall_comment: str = ""
