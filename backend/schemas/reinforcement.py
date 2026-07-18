from pydantic import BaseModel, Field


class ReinforcementGenerateRequest(BaseModel):
    """生成专项巩固习题。"""

    knowledge_point: str = Field(
        min_length=1,
        max_length=200,
    )

    count: int = Field(
        default=3,
        ge=1,
        le=5,
    )


class ReinforcementCheckRequest(BaseModel):
    """检查一道巩固习题的答案。"""

    session_id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    answer: str = ""