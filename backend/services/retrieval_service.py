import math
import re
from collections import Counter

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


def retrieve(query: str, top_k: int = 5) -> list[dict]:
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
                    "document_id": document["id"], "document": document["name"],
                    "content": content, "chunk": index + 1,
                    "score": round(min(.99, .46 + math.log1p(raw_score) / 5), 2),
                })
    rows.sort(key=lambda row: row["score"], reverse=True)
    if not rows:
        for document in store.load()["documents"][:top_k]:
            document_chunks = split_chunks(document["content"])
            if document_chunks:
                rows.append({"document_id": document["id"], "document": document["name"], "content": document_chunks[0], "chunk": 1, "score": .32})
    return rows[:top_k]
