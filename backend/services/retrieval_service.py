import re
from collections import Counter

from services.embedding_service import embed_texts
from services.vector_store import clear_vectors, query_vectors, replace_document_vectors
from storage.json_store import store


def tokenize(text: str) -> list[str]:
    return re.findall(r"[\u4e00-\u9fff]|[a-zA-Z0-9]+", text.lower())


def split_chunks(text: str, size: int = 150) -> list[str]:
    parts = [part.strip() for part in re.split(r"(?<=[。！？；\n])", text) if part.strip()]
    result, current = [], ""
    for part in parts:
        if current and len(current) + len(part) > size:
            result.append(current)
            current = part
        else:
            current += part
    if current:
        result.append(current)
    return result


async def index_document(document: dict) -> int:
    chunks = split_chunks(document["content"])
    embeddings = await embed_texts(chunks)
    rows = []
    for index, (content, embedding) in enumerate(zip(chunks, embeddings), 1):
        rows.append({
            "id": f"{document['id']}-{index}",
            "document_id": document["id"],
            "document": document["name"],
            "chunk": index,
            "content": content,
            "embedding": embedding,
        })
    replace_document_vectors(document["id"], rows)
    return len(rows)


async def rebuild_all_vectors() -> int:
    clear_vectors()
    total = 0
    for document in store.load()["documents"]:
        total += await index_document(document)
    return total


async def retrieve(query: str, top_k: int = 5) -> list[dict]:
    query_embeddings = await embed_texts([query])
    if not query_embeddings:
        return []
    return enrich_source_pages(query_vectors(query_embeddings[0], top_k))


def infer_page(document_content: str, chunk_content: str) -> int | None:
    if not document_content or not chunk_content:
        return None

    probe = chunk_content.strip()[:80]
    direct_page = re.match(r"\s*第\s*(\d+)\s*页", chunk_content)
    if direct_page:
        return int(direct_page.group(1))

    position = document_content.find(probe)
    if position < 0:
        compact_probe = re.sub(r"\s+", "", probe)
        compact_document = re.sub(r"\s+", "", document_content)
        compact_position = compact_document.find(compact_probe)
        if compact_position < 0:
            return None
        position = compact_position

    prefix = document_content[:position]
    matches = list(re.finditer(r"第\s*(\d+)\s*页", prefix))
    if not matches:
        return None
    return int(matches[-1].group(1))


def enrich_source_pages(rows: list[dict]) -> list[dict]:
    documents = {item["id"]: item for item in store.load()["documents"]}
    for row in rows:
        document = documents.get(row.get("document_id"))
        if document:
            row["page"] = infer_page(document.get("content", ""), row.get("content", ""))
    return rows


def keyword_retrieve(query: str, top_k: int = 5) -> list[dict]:
    """保留旧版关键词检索，方便对比和调试。正式问答默认使用向量检索。"""
    query_terms = Counter(tokenize(query))
    rows = []
    for document in store.load()["documents"]:
        for index, content in enumerate(split_chunks(document["content"])):
            content_terms = Counter(tokenize(content))
            overlap = sum(min(query_terms[key], content_terms[key]) for key in query_terms)
            fuzzy = sum(1 for key in query_terms if len(key) > 1 and key in content.lower())
            raw_score = overlap + fuzzy * 2
            if raw_score:
                rows.append({
                    "document_id": document["id"],
                    "document": document["name"],
                    "content": content,
                    "chunk": index + 1,
                    "score": round(raw_score, 2),
                })
    rows.sort(key=lambda row: row["score"], reverse=True)
    if not rows:
        for document in store.load()["documents"][:top_k]:
            document_chunks = split_chunks(document["content"])
            if document_chunks:
                rows.append({
                    "document_id": document["id"],
                    "document": document["name"],
                    "content": document_chunks[0],
                    "chunk": 1,
                    "score": .32,
                })
    return enrich_source_pages(rows[:top_k])
