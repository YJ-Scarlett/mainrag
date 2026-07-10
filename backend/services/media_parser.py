from functools import lru_cache
from pathlib import Path
import re

from fastapi import HTTPException

from core.config import settings


AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".wmv", ".flv"}
SUPPORTED_MEDIA_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS

CLAUSE_WORDS = (
    "首先", "其次", "然后", "接着", "最后", "所以", "因此", "但是", "不过", "另外", "比如",
    "例如", "也就是说", "换句话说", "需要注意", "简单来说", "总的来说",
)


def _punctuate_text(text: str) -> str:
    """轻量标点恢复：先按常见语义连接词断句，再按长度兜底。"""
    cleaned = re.sub(r"\s+", "", text or "").strip("，。！？；、 ")
    if not cleaned:
        return ""
    for word in CLAUSE_WORDS:
        cleaned = cleaned.replace(word, f"，{word}")
    cleaned = re.sub(r"，+", "，", cleaned).strip("，")

    parts = [part for part in re.split(r"([，。！？；])", cleaned) if part]
    result: list[str] = []
    current = ""
    for part in parts:
        current += part
        if part in "，。！？；" or len(current) >= 42:
            result.append(current.rstrip("，；") + ("。" if current[-1] not in "。！？" else ""))
            current = ""
    if current:
        result.append(current.rstrip("，；") + "。")
    return "".join(result)


def _seconds(value) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def _segment_rows(result: dict) -> list[dict]:
    rows = []
    for chunk in result.get("chunks") or []:
        timestamp = chunk.get("timestamp") or chunk.get("timestamps") or (None, None)
        if not isinstance(timestamp, (list, tuple)) or len(timestamp) < 2:
            continue
        text = _punctuate_text(chunk.get("text", ""))
        if not text:
            continue
        rows.append({
            "start": _seconds(timestamp[0]),
            "end": _seconds(timestamp[1]),
            "text": text,
        })
    if rows:
        return rows

    text = _punctuate_text(result.get("text", ""))
    return [{"start": 0.0, "end": 0.0, "text": text}] if text else []


@lru_cache(maxsize=1)
def _speech_pipeline():
    try:
        import torch
        from transformers import pipeline
    except ImportError as exc:
        raise HTTPException(
            500,
            "缺少音视频转写依赖，请确认 torch 和 transformers 已安装。",
        ) from exc

    device = -1
    if settings.embedding_device.lower() == "cuda" and torch.cuda.is_available():
        device = 0

    try:
        return pipeline(
            "automatic-speech-recognition",
            model=settings.local_speech_model,
            device=device,
            model_kwargs={"cache_dir": str(settings.embedding_cache_dir)},
        )
    except Exception as exc:
        raise HTTPException(
            500,
            f"语音识别模型加载失败：{exc}。可在终端设置 LOCAL_SPEECH_MODEL，或检查 Hugging Face 模型缓存。",
        ) from exc


def transcribe_media(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_MEDIA_EXTENSIONS:
        raise HTTPException(400, "仅支持常见音频和视频文件。")

    recognizer = _speech_pipeline()
    kwargs = {}
    if settings.speech_language:
        kwargs = {"generate_kwargs": {"language": settings.speech_language, "task": "transcribe"}}

    try:
        result = recognizer(
            str(path),
            chunk_length_s=30,
            stride_length_s=5,
            return_timestamps=True,
            **kwargs,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            500,
            "音视频转写需要安装 ffmpeg，并确保 ffmpeg 命令可在终端直接运行。",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            400,
            f"音视频转写失败：{exc}。请确认文件未损坏，并已安装 ffmpeg。",
        ) from exc

    if not isinstance(result, dict):
        result = {"text": str(result)}

    segments = _segment_rows(result)
    if not segments:
        return ""

    lines = ["[[PAGE:1]]", "音视频转写内容："]
    for segment in segments:
        lines.append(f"[[TIME:{segment['start']:.2f}-{segment['end']:.2f}]]")
        lines.append(segment["text"])
    return "\n".join(lines)
