from fastapi import APIRouter, HTTPException
from schemas.auth import LoginRequest
from pydantic import BaseModel
import hashlib
import json
from pathlib import Path

router = APIRouter()

# ============ 数据存储路径 ============
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
USER_FILE = DATA_DIR / "users.json"

# ============ 用户数据操作 ============
def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

def load_users():
    if not USER_FILE.exists():
        # 初始化默认账号
        default_users = [
            {"username": "teacher", "password": hash_password("123456"), "name": "陈老师", "role": "teacher"},
            {"username": "student", "password": hash_password("123456"), "name": "张同学", "role": "student"},
        ]
        save_users(default_users)
        return default_users
    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# ============ 请求模型 ============
class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str  # "student" 或 "teacher"
    name: str  # 真实姓名

# ============ 登录接口 ============
@router.post("/login", tags=["认证"])
def login(body: LoginRequest):
    users = load_users()
    user = next((u for u in users if u["username"] == body.username), None)
    if not user:
        raise HTTPException(401, "账号或密码错误")
    if user["password"] != hash_password(body.password):
        raise HTTPException(401, "账号或密码错误")
    if user["role"] != body.role:
        raise HTTPException(401, "角色不匹配，请检查身份选择")
    return {
        "token": f"demo-{body.role}",
        "user": {
            "name": user["name"],
            "role": user["role"],
            "username": user["username"]
        }
    }

# ============ 注册接口（新增）============
@router.post("/register", tags=["认证"])
def register(body: RegisterRequest):
    users = load_users()
    if any(u["username"] == body.username for u in users):
        raise HTTPException(400, "用户名已存在")
    new_user = {
        "username": body.username,
        "password": hash_password(body.password),
        "name": body.name,
        "role": body.role
    }
    users.append(new_user)
    save_users(users)
    return {
        "message": "注册成功",
        "user": {
            "username": body.username,
            "name": body.name,
            "role": body.role
        }
    }

# ============ （可选）查看所有用户（调试用）============
@router.get("/users", tags=["认证"])
def list_users():
    users = load_users()
    return [{"username": u["username"], "name": u["name"], "role": u["role"]} for u in users]