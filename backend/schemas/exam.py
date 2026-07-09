from pydantic import BaseModel, Field


class GenerateExamRequest(BaseModel):
    document_id: str
    chapter: str = "全文"
    title: str = ""
    count: int = Field(default=5, ge=1, le=20)
    difficulty: str = "中等"
    question_types: list[str] = Field(default_factory=lambda: ["choice", "fill", "solution"])


class PublishExamRequest(BaseModel):
    question_ids: list[str] = []


class SubmitExamRequest(BaseModel):
    student: str = "张同学"
    answers: dict[str, str]
