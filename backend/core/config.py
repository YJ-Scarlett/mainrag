import os
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent


@dataclass(frozen=True)
class Settings:
    backend_dir: Path = BACKEND_DIR
    project_dir: Path = PROJECT_DIR
    data_dir: Path = BACKEND_DIR / "data"
    upload_dir: Path = BACKEND_DIR / "uploads"
    database_file: Path = BACKEND_DIR / "data" / "store.json"
    vector_file: Path = BACKEND_DIR / "data" / "vector_store.json"
    vector_db_dir: Path = BACKEND_DIR / "data" / "chroma"
    frontend_dist: Path = PROJECT_DIR / "frontend" / "dist"
    deepseek_api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", "").strip())
    deepseek_base_url: str = field(default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/"))
    deepseek_model: str = field(default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))
    local_embedding_model: str = field(default_factory=lambda: os.getenv("LOCAL_EMBEDDING_MODEL", "BAAI/bge-m3").strip())
    embedding_device: str = field(default_factory=lambda: os.getenv("EMBEDDING_DEVICE", "").strip())
    local_speech_model: str = field(
        default_factory=lambda: os.getenv("LOCAL_SPEECH_MODEL", "openai/whisper-small").strip()
    )
    speech_language: str = field(default_factory=lambda: os.getenv("SPEECH_LANGUAGE", "zh").strip())
    # 修改为 D 盘缓存目录
    embedding_cache_dir: Path = Path("D:/huggingface_cache")
    preview_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("PREVIEW_TIMEOUT_SECONDS", "240")))
    cors_origins: list[str] = field(default_factory=lambda: ["*"])


settings = Settings()
settings.data_dir.mkdir(exist_ok=True)
settings.upload_dir.mkdir(exist_ok=True)
settings.embedding_cache_dir.mkdir(exist_ok=True)
settings.vector_db_dir.mkdir(exist_ok=True)
