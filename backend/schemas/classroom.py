from pydantic import BaseModel, Field


class ClassroomCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class ClassroomStudentAddRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)


class ClassroomTeacherAddRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)


class ClassroomJoinApplyRequest(BaseModel):
    invite_code: str = Field(min_length=4, max_length=20)


class ClassroomJoinReviewRequest(BaseModel):
    note: str = Field(default="", max_length=300)
