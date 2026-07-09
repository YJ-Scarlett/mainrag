import json
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from schemas.chat import ChatRequest
from services.deepseek_service import generate_answer, stream_answer
from services.retrieval_service import retrieve
from storage.json_store import store

router = APIRouter()


LOW_CONFIDENCE_ANSWER = "知识库里暂时没有足够直接的材料。请换一种问法，或请教师补充相关课程资料。"


def _save_chat(student: str, question: str, answer: str, references: list[dict]) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    topic = references[0]["document"] if references else "其他"
    data = store.load()
    data["questions"].append({
        "student": student,
        "question": question,
        "topic": topic,
        "at": now,
    })
    data.setdefault("chat_history", []).append({
        "id": uuid4().hex,
        "student": student,
        "question": question,
        "answer": answer,
        "sources": references,
        "topic": topic,
        "at": now,
    })
    store.save(data)


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(body: ChatRequest):
    references = await retrieve(body.message, 3)
    if not references or references[0]["score"] <= .2:
        answer = LOW_CONFIDENCE_ANSWER
    else:
        answer = await generate_answer(body.message, references)

    _save_chat(body.student, body.message, answer, references)
    return {"answer": answer, "sources": references}


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest):
    async def event_generator():
        references = await retrieve(body.message, 3)
        answer_parts: list[str] = []

        yield _sse({"type": "sources", "sources": references})

        if not references or references[0]["score"] <= .2:
            answer_parts.append(LOW_CONFIDENCE_ANSWER)
            yield _sse({"type": "delta", "content": LOW_CONFIDENCE_ANSWER})
        else:
            try:
                async for delta in stream_answer(body.message, references):
                    answer_parts.append(delta)
                    yield _sse({"type": "delta", "content": delta})
            except Exception as exc:
                error_text = f"\n\n**回答生成失败：** {exc}"
                answer_parts.append(error_text)
                yield _sse({"type": "delta", "content": error_text})

        answer = "".join(answer_parts)
        _save_chat(body.student, body.message, answer, references)
        yield _sse({"type": "done", "answer": answer, "sources": references})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/chat/history")
async def chat_history(student: str = "", limit: int = 30):
    data = store.load()
    items = data.get("chat_history", [])
    if student:
        items = [item for item in items if item.get("student") == student]
    items = sorted(items, key=lambda item: item.get("at", ""), reverse=True)
    return {"items": items[: max(1, min(limit, 100))]}
