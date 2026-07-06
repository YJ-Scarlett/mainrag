from datetime import datetime

from fastapi import APIRouter

from schemas.chat import ChatRequest
from services.deepseek_service import generate_answer
from services.retrieval_service import retrieve
from storage.json_store import store

router = APIRouter()


@router.post("/chat")
async def chat(body: ChatRequest):
    references = retrieve(body.message, 3)
    if not references or references[0]["score"] <= .4:
        answer = "知识库里暂时没有足够直接的材料。请换一种问法，或请教师补充相关课程资料。"
    else:
        answer = await generate_answer(body.message, references)
    data = store.load()
    data["questions"].append({
        "student": body.student, "question": body.message,
        "topic": references[0]["document"] if references else "其他",
        "at": datetime.now().isoformat(timespec="seconds"),
    })
    store.save(data)
    return {"answer": answer, "sources": references}
