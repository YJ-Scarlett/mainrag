import uuid
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile

from core.config import settings
from services.document_parser import SUPPORTED_EXTENSIONS, create_pdf_preview, extract_text
from services.media_parser import SUPPORTED_MEDIA_EXTENSIONS, transcribe_media
from services.retrieval_service import index_document, rebuild_all_vectors, split_chunks
from services.vector_store import delete_document_vectors
from storage.json_store import store

SUPPORTED_UPLOAD_EXTENSIONS = SUPPORTED_EXTENSIONS | SUPPORTED_MEDIA_EXTENSIONS


async def add_document(
    file: UploadFile,
    category: str,
    *,
    owner_teacher_id: str,
    owner_teacher_name: str,
) -> dict:
    raw = await file.read()
    filename = file.filename or "未命名资料"
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise HTTPException(400, "仅支持 DOC、DOCX、PPT、PPTX、PDF、音频和视频文件。")

    target = settings.upload_dir / f"{uuid.uuid4().hex}{suffix}"
    target.write_bytes(raw)

    is_media = suffix in SUPPORTED_MEDIA_EXTENSIONS
    content = transcribe_media(target) if is_media else extract_text(target)
    if not content.strip():
        target.unlink(missing_ok=True)
        raise HTTPException(
            400,
            "文件中未提取到可用于知识库的文字。文档请上传可复制文字的文件；音视频请确认包含清晰语音。",
        )

    item = {
        "id": uuid.uuid4().hex[:10],
        "name": Path(filename).stem,
        "type": category,
        "size": round(len(raw) / 1024, 1),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "content": content[:200000],
        "extension": suffix.lstrip(".").upper(),
        "stored_path": target.name,
        "preview_path": "",
        "preview_status": "failed" if is_media else "processing",
        "preview_error": "音视频资料已完成转写并入库，暂不提供原版式预览。" if is_media else "",
        "source_kind": "media" if is_media else "document",
        "owner_teacher_id": owner_teacher_id,
        "owner_teacher_name": owner_teacher_name,
    }

    await index_document(item)
    data = store.load()
    data["documents"].insert(0, item)
    store.save(data)
    return item


def generate_document_preview(document_id: str) -> None:
    data = store.load()
    document = next((item for item in data["documents"] if item["id"] == document_id), None)
    if not document:
        return

    stored_path = document.get("stored_path")
    if not stored_path:
        return

    target = settings.upload_dir / stored_path
    if target.suffix.lower() in SUPPORTED_MEDIA_EXTENSIONS:
        document["preview_path"] = ""
        document["preview_status"] = "failed"
        document["preview_error"] = "音视频资料已完成转写并入库，暂不提供原版式预览。"
        store.save(data)
        return

    preview = settings.upload_dir / f"{target.stem}-preview.pdf"
    document["preview_status"] = "processing"
    document["preview_error"] = ""
    store.save(data)

    try:
        create_pdf_preview(target, preview)
    except HTTPException as exc:
        data = store.load()
        document = next((item for item in data["documents"] if item["id"] == document_id), None)
        if document:
            document["preview_path"] = ""
            document["preview_status"] = "failed"
            document["preview_error"] = str(exc.detail)
            store.save(data)
        preview.unlink(missing_ok=True)
        return
    except Exception as exc:
        data = store.load()
        document = next((item for item in data["documents"] if item["id"] == document_id), None)
        if document:
            document["preview_path"] = ""
            document["preview_status"] = "failed"
            document["preview_error"] = f"预览生成失败：{exc}"
            store.save(data)
        preview.unlink(missing_ok=True)
        return

    data = store.load()
    document = next((item for item in data["documents"] if item["id"] == document_id), None)
    if document:
        document["preview_path"] = preview.name
        document["preview_status"] = "ready"
        document["preview_error"] = ""
        store.save(data)


def list_documents() -> list[dict]:
    return [
        {
            key: value
            for key, value in item.items()
            if key not in {"content", "stored_path", "preview_path"}
        } | {
            "chunks": len(split_chunks(item["content"])),
            "has_preview": bool(item.get("preview_path")),
            "preview_status": item.get("preview_status") or ("ready" if item.get("preview_path") else "failed"),
        }
        for item in store.load()["documents"]
    ]


def get_document(document_id: str) -> dict:
    document = next((item for item in store.load()["documents"] if item["id"] == document_id), None)
    if not document:
        raise HTTPException(404, "知识库资料不存在。")
    return document


def get_preview_path(document_id: str) -> Path:
    document = get_document(document_id)
    filename = document.get("preview_path")
    if not filename:
        if document.get("preview_status") == "processing":
            raise HTTPException(409, "预览正在后台生成中，请稍后再试。")
        if document.get("preview_status") == "failed":
            raise HTTPException(404, document.get("preview_error") or "预览生成失败。")
        raise HTTPException(404, "该资料没有原文版式预览，但仍可用于知识库检索和问答。")
    path = (settings.upload_dir / filename).resolve()
    if settings.upload_dir.resolve() not in path.parents or not path.is_file():
        raise HTTPException(404, "预览文件不存在。")
    return path


def get_media_path(document_id: str) -> Path:
    document = get_document(document_id)
    stored_path = document.get("stored_path")
    if document.get("source_kind") != "media" or not stored_path:
        raise HTTPException(404, "该资料不是音视频文件。")

    path = (settings.upload_dir / stored_path).resolve()
    if settings.upload_dir.resolve() not in path.parents or not path.is_file():
        raise HTTPException(404, "音视频文件不存在。")
    if path.suffix.lower() not in SUPPORTED_MEDIA_EXTENSIONS:
        raise HTTPException(404, "该资料不是支持预览的音视频格式。")
    return path


def get_download_path(document_id: str) -> tuple[Path, str]:
    document = get_document(document_id)
    stored_path = document.get("stored_path")
    if not stored_path:
        raise HTTPException(404, "原始文件不存在。")

    path = (settings.upload_dir / stored_path).resolve()
    if settings.upload_dir.resolve() not in path.parents or not path.is_file():
        raise HTTPException(404, "原始文件不存在。")

    suffix = path.suffix or f".{str(document.get('extension') or '').lower()}"
    filename = f"{document.get('name') or path.stem}{suffix}"
    return path, filename


def delete_document(document_id: str, requester_teacher_id: str) -> None:
    data = store.load()
    document = next((item for item in data["documents"] if item["id"] == document_id), None)
    remaining = [item for item in data["documents"] if item["id"] != document_id]
    if len(remaining) == len(data["documents"]):
        raise HTTPException(404, "资料不存在。")
    if document.get("owner_teacher_id") != requester_teacher_id:
        raise HTTPException(403, "只能删除自己上传的资料。")
    data["documents"] = remaining
    store.save(data)
    delete_document_vectors(document_id)
    for key in ("stored_path", "preview_path"):
        if document and document.get(key):
            path = (settings.upload_dir / document[key]).resolve()
            if settings.upload_dir.resolve() in path.parents:
                path.unlink(missing_ok=True)


async def rebuild_knowledge_vectors() -> dict:
    data = store.load()
    changed = False
    for document in data["documents"]:
        if document.get("source_kind") != "media" or "[[TIME:" in (document.get("content") or ""):
            continue
        stored_path = document.get("stored_path")
        if not stored_path:
            continue
        target = settings.upload_dir / stored_path
        if target.exists():
            document["content"] = transcribe_media(target)[:200000]
            changed = True
    if changed:
        store.save(data)
    total = await rebuild_all_vectors()
    return {"documents": len(store.load()["documents"]), "chunks": total}
