import sys
from contextlib import asynccontextmanager

sys.path.append(r"D:\python_libs")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import api_router
from core.config import settings
from db.database import init_database
from services.migration_service import run_startup_migrations
from web.frontend import mount_frontend


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    app.state.migration_report = run_startup_migrations()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="知问课堂 API",
        version="1.2.0",
        lifespan=lifespan,
    )
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
