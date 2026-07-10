import os
from functools import lru_cache

from fastapi import HTTPException

from core.config import settings


def _resolve_local_bge_m3() -> str:
    """优先使用本地 BGE-M3 snapshot，避免访问 HuggingFace。"""
    if settings.local_embedding_model not in {"BAAI/bge-m3", "BAAI/bge-m3/"}:
        return settings.local_embedding_model

    search_roots = [
        settings.embedding_cache_dir,
        settings.backend_dir / "models",
    ]
    for cache_dir in search_roots:
        snapshot_root = cache_dir / "models--BAAI--bge-m3" / "snapshots"
        if not snapshot_root.exists():
            continue

        candidates = sorted(snapshot_root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        for snapshot in candidates:
            if (
                snapshot.is_dir()
                and (snapshot / "modules.json").is_file()
                and (snapshot / "config_sentence_transformers.json").is_file()
            ):
                return str(snapshot)

    return settings.local_embedding_model


@lru_cache(maxsize=1)
def _load_sentence_transformer():
    """加载本地 embedding 模型，不需要 embedding 密钥。"""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise HTTPException(
            503,
            "缺少 sentence-transformers，无法加载本地 BGE-M3。请先执行：python -m pip install -r requirements.txt",
        ) from exc

    model_name_or_path = _resolve_local_bge_m3()
    kwargs = {"cache_folder": str(settings.embedding_cache_dir), "local_files_only": True}
    if settings.embedding_device:
        kwargs["device"] = settings.embedding_device

    try:
        return SentenceTransformer(model_name_or_path, **kwargs)
    except Exception as exc:
        raise HTTPException(
            503,
            "本地 BGE-M3 模型加载失败。请确认 backend/models 或 D:/huggingface_cache 中已经完整下载 BAAI/bge-m3。"
            f"当前尝试路径：{model_name_or_path}。原始错误：{exc}",
        ) from exc


async def embed_texts(texts: list[str]) -> list[list[float]]:
    clean_texts = [text.strip() for text in texts if text and text.strip()]
    if not clean_texts:
        return []

    model = _load_sentence_transformer()
    try:
        vectors = model.encode(
            clean_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [vector.tolist() for vector in vectors]
    except Exception as exc:
        raise HTTPException(502, f"本地 BGE-M3 向量化失败：{exc}") from exc
