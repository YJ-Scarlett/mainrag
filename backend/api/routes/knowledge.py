import mimetypes

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse

from core.security import require_teacher
from services.document_service import (
    add_document,
    delete_document,
    generate_document_preview,
    get_document,
    get_download_path,
    get_media_path,
    get_preview_path,
    list_documents,
    rebuild_knowledge_vectors,
)

router = APIRouter()


@router.get("")
def get_documents():
    return {"items": list_documents()}


@router.get("/{document_id}")
def get_document_detail(document_id: str):
    document = get_document(document_id)
    public_document = {
        key: value
        for key, value in document.items()
        if key not in {"stored_path", "preview_path"}
    }
    return public_document | {"has_preview": bool(document.get("preview_path"))}


@router.get("/{document_id}/preview")
def preview_document(document_id: str):
    path = get_preview_path(document_id)
    return FileResponse(
        path,
        media_type="application/pdf",
        content_disposition_type="inline",
        filename=path.name,
    )


@router.get("/{document_id}/media")
def preview_media(document_id: str):
    path = get_media_path(document_id)
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(
        path,
        media_type=media_type,
        content_disposition_type="inline",
        filename=path.name,
    )


@router.get("/{document_id}/download")
def download_document(document_id: str):
    path, filename = get_download_path(document_id)
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(
        path,
        media_type=media_type,
        content_disposition_type="attachment",
        filename=filename,
    )


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form("课程资料"),
    _: None = Depends(require_teacher),
):
    item = await add_document(file, category)
    background_tasks.add_task(generate_document_preview, item["id"])
    public_item = {
        key: value
        for key, value in item.items()
        if key not in {"content", "stored_path", "preview_path"}
    } | {"has_preview": bool(item.get("preview_path"))}
    message = "上传、转写并建立向量索引成功，可在线播放预览" if item.get("source_kind") == "media" else "上传、解析并建立向量索引成功，预览正在后台生成"
    return {"message": message, "item": public_item}


@router.post("/reindex")
async def reindex_documents(_: None = Depends(require_teacher)):
    result = await rebuild_knowledge_vectors()
    return {"message": "知识库向量索引重建成功", **result}


@router.delete("/{document_id}")
def remove_document(document_id: str, _: None = Depends(require_teacher)):
    delete_document(document_id)
    return {"message": "已删除"}
