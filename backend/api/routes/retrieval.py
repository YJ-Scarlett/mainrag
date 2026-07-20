from typing import Annotated

from fastapi import APIRouter, Depends

from core.security import get_current_user
from db.models import User
from schemas.chat import SearchRequest
from services.retrieval_service import retrieve

router = APIRouter()


@router.post("/search")
async def search(
    body: SearchRequest,
    _: Annotated[User, Depends(get_current_user)],
):
    return {"query": body.query, "results": await retrieve(body.query, body.top_k)}
