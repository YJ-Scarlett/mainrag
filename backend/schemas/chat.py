from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    # 旧前端兼容字段；实际身份始终从 JWT 中读取。
    student: str | None = None
