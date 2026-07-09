from functools import lru_cache

from fastapi import HTTPException

from core.config import settings

COLLECTION_NAME = "mainrag_knowledge"


@lru_cache(maxsize=1)
def get_collection():
    """使用 ChromaDB 作为持久化向量数据库。"""
    try:
        import chromadb
    except ImportError as exc:
        raise HTTPException(
            503,
            "缺少 ChromaDB，无法使用向量数据库。请先安装：python -m pip install chromadb==0.5.23",
        ) from exc

    client = chromadb.PersistentClient(path=str(settings.vector_db_dir))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def replace_document_vectors(document_id: str, rows: list[dict]) -> None:
    collection = get_collection()
    delete_document_vectors(document_id)
    if not rows:
        return

    collection.add(
        ids=[row["id"] for row in rows],
        documents=[row["content"] for row in rows],
        embeddings=[row["embedding"] for row in rows],
        metadatas=[
            {
                "document_id": row["document_id"],
                "document": row["document"],
                "chunk": row["chunk"],
                "page": row.get("page") or 0,
            }
            for row in rows
        ],
    )


def delete_document_vectors(document_id: str) -> None:
    collection = get_collection()
    try:
        collection.delete(where={"document_id": document_id})
    except Exception:
        pass


def clear_vectors() -> None:
    collection = get_collection()
    try:
        collection.delete()
    except Exception:
        pass


def query_vectors(query_embedding: list[float], top_k: int = 5) -> list[dict]:
    collection = get_collection()
    if not query_embedding:
        return []

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=max(1, top_k),
        include=["documents", "metadatas", "distances"],
    )
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    rows = []
    for content, metadata, distance in zip(documents, metadatas, distances):
        score = max(0.0, min(1.0, 1 - float(distance)))
        rows.append({
            "document_id": metadata.get("document_id"),
            "document": metadata.get("document"),
            "content": content,
            "chunk": metadata.get("chunk"),
            "page": metadata.get("page") or None,
            "score": round(score, 4),
        })
    return rows
