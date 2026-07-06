import uuid
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile
from core.config import settings
from services.document_parser import SUPPORTED_EXTENSIONS, create_pdf_preview, extract_text
from services.retrieval_service import split_chunks
from storage.json_store import store


async def add_document(file: UploadFile, category: str) -> dict:
    raw = await file.read()
    filename = file.filename or "未命名资料"
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(400, "支持 DOC、DOCX、PPT、PPTX 和 PDF 文件")
    target = settings.upload_dir / f"{uuid.uuid4().hex}{suffix}"
    target.write_bytes(raw)
    content = extract_text(target)
    preview = settings.upload_dir / f"{target.stem}-preview.pdf"
    create_pdf_preview(target, preview)
    if not content.strip():
        raise HTTPException(400, "文件中未提取到文本")
    item = {
        "id": uuid.uuid4().hex[:10], "name": Path(filename).stem, "type": category,
        "size": round(len(raw) / 1024, 1), "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "content": content[:200000],
        "extension": suffix.lstrip(".").upper(),
        "stored_path": target.name,
        "preview_path": preview.name,
    }
    data = store.load()
    data["documents"].insert(0, item)
    store.save(data)
    return item


def list_documents() -> list[dict]:
    return [
        {key: value for key, value in item.items() if key not in {"content", "stored_path", "preview_path"}} | {"chunks": len(split_chunks(item["content"])), "has_preview": bool(item.get("preview_path"))}
        for item in store.load()["documents"]
    ]


def get_document(document_id: str) -> dict:
    document = next((item for item in store.load()["documents"] if item["id"] == document_id), None)
    if not document:
        raise HTTPException(404, "知识库资料不存在")
    return document


def get_preview_path(document_id: str) -> Path:
    document = get_document(document_id)
    filename = document.get("preview_path")
    if not filename:
        raise HTTPException(404, "该演示资料没有原文件预览，请重新上传原始文档")
    path = (settings.upload_dir / filename).resolve()
    if settings.upload_dir.resolve() not in path.parents or not path.is_file():
        raise HTTPException(404, "预览文件不存在")
    return path


def delete_document(document_id: str) -> None:
    data = store.load()
    document = next((item for item in data["documents"] if item["id"] == document_id), None)
    remaining = [item for item in data["documents"] if item["id"] != document_id]
    if len(remaining) == len(data["documents"]):
        raise HTTPException(404, "资料不存在")
    data["documents"] = remaining
    store.save(data)
    for key in ("stored_path", "preview_path"):
        if document and document.get(key):
            path = (settings.upload_dir / document[key]).resolve()
            if settings.upload_dir.resolve() in path.parents:
                path.unlink(missing_ok=True)
