import json
import math
import threading
from pathlib import Path

from core.config import settings

_lock = threading.RLock()


def _initial_data() -> dict:
    return {"items": []}


def load_vectors() -> dict:
    with _lock:
        path = settings.vector_file
        if not path.exists():
            save_vectors(_initial_data())
        return json.loads(path.read_text(encoding="utf-8"))


def save_vectors(data: dict) -> None:
    with _lock:
        path = settings.vector_file
        path.parent.mkdir(exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)


def replace_document_vectors(document_id: str, rows: list[dict]) -> None:
    data = load_vectors()
    data["items"] = [item for item in data.get("items", []) if item.get("document_id") != document_id]
    data["items"].extend(rows)
    save_vectors(data)


def delete_document_vectors(document_id: str) -> None:
    data = load_vectors()
    data["items"] = [item for item in data.get("items", []) if item.get("document_id") != document_id]
    save_vectors(data)


def clear_vectors() -> None:
    save_vectors(_initial_data())


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)
