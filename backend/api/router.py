from fastapi import APIRouter

from api.routes import (
    analysis,
    auth,
    chat,
    exams,
    health,
    knowledge,
    reinforcement,
    retrieval,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["知识库"])
api_router.include_router(retrieval.router, tags=["检索"])
api_router.include_router(chat.router, tags=["问答"])
api_router.include_router(exams.router, prefix="/exams", tags=["习题"])
api_router.include_router(
    reinforcement.router,
    prefix="/reinforcement",
    tags=["专项巩固"],
)
api_router.include_router(analysis.router, prefix="/analysis", tags=["学情分析"])
