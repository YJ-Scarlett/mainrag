from fastapi import APIRouter

from schemas.chat import SearchRequest
from services.retrieval_service import retrieve

router = APIRouter()


@router.post("/search")
async def search(body: SearchRequest):
    return {"query": body.query, "results": await retrieve(body.query, body.top_k)}
