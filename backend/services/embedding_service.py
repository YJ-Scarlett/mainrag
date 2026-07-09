from functools import lru_cache

from fastapi import HTTPException

from core.config import settings


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

    kwargs = {"cache_folder": str(settings.embedding_cache_dir)}
    if settings.embedding_device:
        kwargs["device"] = settings.embedding_device
    return SentenceTransformer(settings.local_embedding_model, **kwargs)


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
