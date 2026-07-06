from fastapi import APIRouter

from schemas.chat import SearchRequest
from services.retrieval_service import retrieve

router = APIRouter()


@router.post("/search")
def search(body: SearchRequest):
    return {"query": body.query, "results": retrieve(body.query, body.top_k)}
