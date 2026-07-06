from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core.config import settings


def mount_frontend(app: FastAPI) -> None:
    """托管前端构建产物，并为前端页面路由提供 SPA 回退。"""
    if not settings.frontend_dist.exists():
        return
    assets = settings.frontend_dist / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="frontend-assets")

    @app.get("/{page_path:path}", include_in_schema=False)
    async def frontend_page(page_path: str):
        requested = (settings.frontend_dist / page_path).resolve()
        if requested.is_file() and settings.frontend_dist.resolve() in requested.parents:
            return FileResponse(requested)
        return FileResponse(settings.frontend_dist / "index.html")
