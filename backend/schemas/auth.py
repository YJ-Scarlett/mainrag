from typing import Literal
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str
    role: Literal["teacher", "student"]
