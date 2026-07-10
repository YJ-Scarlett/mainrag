import os
import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile


SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


async def save_temp_image(file: UploadFile) -> Path:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_IMAGE_EXTENSIONS:
        raise HTTPException(400, "请上传 JPG、PNG、BMP 或 WEBP 格式的题目图片")

    data = await file.read()
    if not data:
        raise HTTPException(400, "图片为空，请重新上传")
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(400, "图片不能超过 8MB")

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        temp.write(data)
        return Path(temp.name)
    finally:
        temp.close()


def _ocr_with_paddle(image_path: Path) -> str:
    os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
    os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "0")
    os.environ.setdefault("FLAGS_use_onednn", "0")
    os.environ.setdefault("FLAGS_use_mkldnn", "0")
    os.environ.setdefault("FLAGS_enable_pir_api", "0")
    os.environ.setdefault("FLAGS_enable_pir_in_executor", "0")

    from paddleocr import PaddleOCR  # type: ignore

    try:
        ocr = PaddleOCR(
            lang="ch",
            ocr_version="PP-OCRv4",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
    except TypeError:
        ocr = PaddleOCR(use_angle_cls=False, lang="ch")

    if hasattr(ocr, "predict"):
        result = ocr.predict(input=str(image_path))
    else:
        result = ocr.ocr(str(image_path), cls=True)

    lines: list[str] = []

    def collect_text(obj) -> None:
        if obj is None:
            return
        if isinstance(obj, str):
            text = obj.strip()
            if text:
                lines.append(text)
            return
        if isinstance(obj, dict):
            for key in ("rec_texts", "texts"):
                value = obj.get(key)
                if isinstance(value, list):
                    for item in value:
                        collect_text(item)
                    return
            for key in ("text", "rec_text", "transcription"):
                value = obj.get(key)
                if isinstance(value, str):
                    collect_text(value)
                    return
            for value in obj.values():
                collect_text(value)
            return
        if isinstance(obj, (list, tuple)):
            if len(obj) >= 2 and isinstance(obj[1], (list, tuple)) and obj[1] and isinstance(obj[1][0], str):
                collect_text(obj[1][0])
                return
            for item in obj:
                collect_text(item)
            return
        for method in ("to_dict", "json"):
            func = getattr(obj, method, None)
            if callable(func):
                try:
                    collect_text(func())
                    return
                except Exception:
                    pass

    collect_text(result)
    return "\n".join(line for line in lines if line)


def _ocr_with_tesseract(image_path: Path) -> str:
    import pytesseract  # type: ignore
    from PIL import Image  # type: ignore

    with Image.open(image_path) as image:
        return pytesseract.image_to_string(image, lang="chi_sim+eng").strip()


def clean_ocr_text(text: str) -> str:
    rows = [row.strip() for row in (text or "").replace("\r", "\n").split("\n")]
    rows = [row for row in rows if row]
    return "\n".join(rows).strip()


async def extract_question_text(file: UploadFile) -> str:
    image_path = await save_temp_image(file)
    errors: list[str] = []
    try:
        for name, runner in (("PaddleOCR", _ocr_with_paddle), ("Tesseract OCR", _ocr_with_tesseract)):
            try:
                text = clean_ocr_text(runner(image_path))
                if text:
                    return text
            except ImportError as exc:
                errors.append(f"{name} 未安装：{exc}")
            except Exception as exc:
                errors.append(f"{name} 识别失败：{exc}")

        detail = (
            "图片文字识别失败。请先安装一种 OCR 方案：\n"
            "1. 推荐 PaddleOCR：python -m pip install paddleocr paddlepaddle\n"
            "2. 或 Tesseract：python -m pip install pillow pytesseract，并安装系统版 Tesseract OCR\n"
            f"调试信息：{'；'.join(errors)}"
        )
        raise HTTPException(503, detail)
    finally:
        try:
            image_path.unlink(missing_ok=True)
        except Exception:
            pass
