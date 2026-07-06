from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse

from core.security import require_teacher
from services.document_service import add_document, delete_document, get_document, get_preview_path, list_documents

router = APIRouter()


@router.get("")
def get_documents():
    return {"items": list_documents()}


@router.get("/{document_id}")
def get_document_detail(document_id: str):
    document = get_document(document_id)
    return {key: value for key, value in document.items() if key not in {"stored_path", "preview_path"}} | {"has_preview": bool(document.get("preview_path"))}


@router.get("/{document_id}/preview")
def preview_document(document_id: str):
    path = get_preview_path(document_id)
    return FileResponse(path, media_type="application/pdf", content_disposition_type="inline", filename=path.name)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), category: str = Form("课程资料"), _: None = Depends(require_teacher)):
    item = await add_document(file, category)
    public_item = {key: value for key, value in item.items() if key != "content"}
    return {"message": "上传并建立索引成功", "item": public_item}


@router.delete("/{document_id}")
def remove_document(document_id: str, _: None = Depends(require_teacher)):
    delete_document(document_id)
    return {"message": "已删除"}
