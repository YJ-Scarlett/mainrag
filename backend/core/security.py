from fastapi import Header, HTTPException


def require_teacher(x_role: str | None = Header(default=None)) -> None:
    """轻量演示权限校验；生产环境应替换为签名 JWT。"""
    if x_role != "teacher":
        raise HTTPException(403, "仅教师可以修改知识库")
