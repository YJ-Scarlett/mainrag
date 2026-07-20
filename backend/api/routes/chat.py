import json
from datetime import datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from core.config import settings
from core.security import get_current_user
from db.models import User
from schemas.chat import ChatRequest
from services.deepseek_service import generate_answer, stream_answer
from services.identity_service import record_belongs_to_user, user_legacy_label
from services.photo_ocr_service import (
    SUPPORTED_IMAGE_EXTENSIONS,
    extract_question_text_from_path,
)
from services.retrieval_service import retrieve
from storage.json_store import store

router = APIRouter()

LOW_CONFIDENCE_ANSWER = "知识库里暂时没有足够直接的材料。请换一种问法，或请教师补充相关课程资料。"
CHAT_IMAGE_DIR = settings.upload_dir / "chat-images"
CHAT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def _save_chat(
    user: User,
    question: str,
    answer: str,
    references: list[dict],
    *,
    kind: str = "chat",
    ocr_text: str = "",
    image_url: str = "",
) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    topic = references[0]["document"] if references else "其他"
    legacy_label = user_legacy_label(user)
    data = store.load()
    data["questions"].append(
        {
            "user_id": user.id,
            "user_name": user.name,
            "student": legacy_label,
            "question": question,
            "topic": topic,
            "at": now,
        }
    )
    data.setdefault("chat_history", []).append(
        {
            "id": uuid4().hex,
            "user_id": user.id,
            "user_name": user.name,
            "student": legacy_label,
            "question": question,
            "answer": answer,
            "sources": references,
            "topic": topic,
            "at": now,
            "kind": kind,
            "ocr_text": ocr_text,
            "image_url": image_url,
        }
    )
    store.save(data)


async def _get_references(query: str, top_k: int = 3) -> list[dict]:
    return await retrieve(query, top_k)


async def _save_chat_image(file: UploadFile) -> tuple[Path, str]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_IMAGE_EXTENSIONS:
        raise HTTPException(400, "请上传 JPG、PNG、BMP 或 WEBP 格式的题目图片")
    data = await file.read()
    if not data:
        raise HTTPException(400, "图片为空，请重新上传")
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(400, "图片不能超过 8MB")
    filename = f"{uuid4().hex}{suffix}"
    image_path = CHAT_IMAGE_DIR / filename
    image_path.write_bytes(data)
    return image_path, f"/api/chat/photo/{filename}"


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(
    body: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    references = await _get_references(body.message, 3)
    if not references or references[0]["score"] <= 0.2:
        answer = LOW_CONFIDENCE_ANSWER
    else:
        answer = await generate_answer(body.message, references)

    _save_chat(current_user, body.message, answer, references)
    return {"answer": answer, "sources": references}


@router.post("/chat/stream")
async def chat_stream(
    body: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    async def event_generator():
        references = await _get_references(body.message, 3)
        answer_parts: list[str] = []

        yield _sse({"type": "sources", "sources": references})

        if not references or references[0]["score"] <= 0.2:
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
        _save_chat(current_user, body.message, answer, references)
        yield _sse({"type": "done", "answer": answer, "sources": references})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/chat/photo-search")
async def photo_search(
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
):
    image_path, image_url = await _save_chat_image(file)
    try:
        ocr_text = extract_question_text_from_path(image_path, cleanup=False)
        question = (
            "请根据下面拍照识别出的题目进行解答。"
            "如果是选择题，请给出正确选项和理由；如果是填空题或解答题，请给出步骤和结论。\n\n"
            f"题目内容：\n{ocr_text}"
        )
        references = await _get_references(ocr_text, 3)
        if not references or references[0]["score"] <= 0.2:
            answer = LOW_CONFIDENCE_ANSWER
        else:
            answer = await generate_answer(question, references)
        _save_chat(
            current_user,
            f"拍照搜题：\n{ocr_text}",
            answer,
            references,
            kind="photo_search",
            ocr_text=ocr_text,
            image_url=image_url,
        )
        return {
            "ocr_text": ocr_text,
            "question": question,
            "answer": answer,
            "sources": references,
            "image_url": image_url,
        }
    except Exception:
        try:
            image_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise


# 图片由 <img> 直接加载，第一阶段暂时保持该资源接口公开；后续可改为短期签名 URL。
@router.get("/chat/photo/{filename}")
async def get_chat_photo(filename: str):
    safe_name = Path(filename).name
    image_path = (CHAT_IMAGE_DIR / safe_name).resolve()
    if CHAT_IMAGE_DIR.resolve() not in image_path.parents or not image_path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")
    return FileResponse(image_path)


@router.get("/chat/history")
async def chat_history(
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 30,
):
    data = store.load()
    items = [
        item
        for item in data.get("chat_history", [])
        if record_belongs_to_user(
            item,
            current_user,
            id_fields=("user_id", "student_id"),
        )
    ]
    items = sorted(items, key=lambda item: item.get("at", ""), reverse=True)
    limited_items = items[: max(1, min(limit, 100))]

    changed = False
    for item in limited_items:
        is_photo = (
            item.get("kind") == "photo_search"
            or item.get("ocr_text")
            or str(item.get("question", "")).startswith("拍照搜题")
        )
        query = item.get("ocr_text") or str(item.get("question", "")).replace(
            "拍照搜题：",
            "",
        ).strip()
        if is_photo and query:
            refreshed_sources = await _get_references(query, 3)
            if refreshed_sources:
                item["sources"] = refreshed_sources
                changed = True
    if changed:
        store.save(data)
    return {"items": limited_items}


@router.delete("/chat/history/{history_id}")
async def delete_chat_history(
    history_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    data = store.load()
    items = data.get("chat_history", [])
    kept = []
    deleted = None

    for item in items:
        if (
            item.get("id") == history_id
            and record_belongs_to_user(
                item,
                current_user,
                id_fields=("user_id", "student_id"),
            )
        ):
            deleted = item
            continue
        kept.append(item)

    if deleted is None:
        raise HTTPException(status_code=404, detail="历史问答不存在或无权删除")

    data["chat_history"] = kept
    store.save(data)

    image_url = deleted.get("image_url") or ""
    if image_url.startswith("/api/chat/photo/"):
        image_name = Path(image_url.rsplit("/", 1)[-1]).name
        image_path = CHAT_IMAGE_DIR / image_name
        if image_path.exists():
            try:
                image_path.unlink()
            except Exception:
                pass

    return {"message": "历史问答已删除", "id": history_id}
