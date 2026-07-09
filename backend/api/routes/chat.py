from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from schemas.chat import ChatRequest
from services.deepseek_service import generate_answer, generate_answer_stream
from services.retrieval_service import retrieve
from storage.json_store import store

router = APIRouter()


@router.post("/chat")
async def chat(body: ChatRequest):
    references = await retrieve(body.message, 3)
    if not references or references[0]["score"] <= .2:
        answer = "知识库里暂时没有足够直接的材料。请换一种问法，或请教师补充相关课程资料。"
    else:
        answer = await generate_answer(body.message, references)

    now = datetime.now().isoformat(timespec="seconds")
    topic = references[0]["document"] if references else "其他"
    data = store.load()
    data["questions"].append({
        "student": body.student,
        "question": body.message,
        "topic": topic,
        "at": now,
    })
    data.setdefault("chat_history", []).append({
        "id": uuid4().hex,
        "student": body.student,
        "question": body.message,
        "answer": answer,
        "sources": references,
        "topic": topic,
        "at": now,
    })
    store.save(data)
    return {"answer": answer, "sources": references}


@router.get("/chat/history")
async def chat_history(student: str = "", limit: int = 30):
    data = store.load()
    items = data.get("chat_history", [])
    if student:
        items = [item for item in items if item.get("student") == student]
    items = sorted(items, key=lambda item: item.get("at", ""), reverse=True)
    return {"items": items[: max(1, min(limit, 100))]}

@router.post("/chat/stream")
async def chat_stream(body: ChatRequest):
    references = await retrieve(body.message, 3)
    if not references or references[0]["score"] <= .2:
        async def fallback_stream():
            yield "知识库里暂时没有足够直接的材料。请换一种问法，或请教师补充相关课程资料。"
        return StreamingResponse(fallback_stream(), media_type="text/plain")

    async def generate():
        async for chunk in generate_answer_stream(body.message, references):
            yield chunk
        import json
        yield f"\n[SOURCES]{json.dumps(references, ensure_ascii=False)}"

    return StreamingResponse(generate(), media_type="text/plain")