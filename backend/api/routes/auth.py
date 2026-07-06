from fastapi import APIRouter, HTTPException

from schemas.auth import LoginRequest

router = APIRouter()

ACCOUNTS = {
    "teacher": ("teacher", "123456", "陈老师"),
    "student": ("student", "123456", "张同学"),
}


@router.post("/login", tags=["认证"])
def login(body: LoginRequest):
    account = ACCOUNTS.get(body.role)
    if not account or (body.username, body.password) != account[:2]:
        raise HTTPException(401, "账号、密码或角色不正确")
    return {"token": f"demo-{body.role}", "user": {"name": account[2], "role": body.role}}
