"""兼容入口：`uvicorn app:app`。实际应用装配位于 main.py。"""

from main import app

__all__ = ["app"]
