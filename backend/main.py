from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import api_router
from core.config import settings
from web.frontend import mount_frontend


def create_app() -> FastAPI:
    app = FastAPI(title="知问课堂 API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api")
    mount_frontend(app)
    return app


app = create_app()
