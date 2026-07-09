from functools import lru_cache

from fastapi import HTTPException

from core.config import settings


def _resolve_local_bge_m3() -> str:
    """优先使用已经下载到 backend/models 的 BGE-M3 本地快照，避免联网 HEAD 检查。"""
    if settings.local_embedding_model not in {"BAAI/bge-m3", "BAAI/bge-m3/"}:
        return settings.local_embedding_model

    model_root = settings.embedding_cache_dir / "models--BAAI--bge-m3" / "snapshots"
    if not model_root.exists():
        return settings.local_embedding_model

    candidates = sorted(model_root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
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
    """加载本地 embedding 模型。

    第一次运行时 sentence-transformers 会把 BAAI/bge-m3 下载到 backend/models。
    下载完成后再次启动会直接读取本地缓存，不需要 embedding 密钥。
    """
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
            "本地 BGE-M3 模型加载失败。请确认 backend/models 中已经完整下载 BAAI/bge-m3，"
            "或联网后重新下载模型。原始错误：" + str(exc),
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
