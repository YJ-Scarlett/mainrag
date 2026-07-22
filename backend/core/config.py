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

    # SQLite 保存账号、班级以及系统业务数据；store.json 仅作为旧数据迁移来源保留。
    database_file: Path = BACKEND_DIR / "data" / "store.json"
    auth_database_file: Path = BACKEND_DIR / "data" / "mainrag.sqlite3"
    business_database_file: Path = BACKEND_DIR / "data" / "mainrag.sqlite3"
    legacy_user_file: Path = BACKEND_DIR / "api" / "data" / "users.json"
    backup_dir: Path = BACKEND_DIR / "data" / "backups"
    migration_report_file: Path = BACKEND_DIR / "data" / "migration_report.json"

    vector_file: Path = BACKEND_DIR / "data" / "vector_store.json"
    vector_db_dir: Path = BACKEND_DIR / "data" / "chroma"
    frontend_dist: Path = PROJECT_DIR / "frontend" / "dist"

    jwt_secret_key: str = field(
        default_factory=lambda: os.getenv(
            "MAINRAG_JWT_SECRET_KEY",
            "mainrag-development-secret-change-before-production",
        ).strip()
    )
    jwt_algorithm: str = field(
        default_factory=lambda: os.getenv("MAINRAG_JWT_ALGORITHM", "HS256").strip()
    )
    access_token_minutes: int = field(
        default_factory=lambda: int(os.getenv("MAINRAG_ACCESS_TOKEN_MINUTES", "720"))
    )
    teacher_invite_code: str = field(
        default_factory=lambda: os.getenv("MAINRAG_TEACHER_INVITE_CODE", "").strip()
    )

    deepseek_api_key: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", "").strip()
    )
    deepseek_base_url: str = field(
        default_factory=lambda: os.getenv(
            "DEEPSEEK_BASE_URL",
            "https://api.deepseek.com",
        ).rstrip("/")
    )
    deepseek_model: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    )
    local_embedding_model: str = field(
        default_factory=lambda: os.getenv(
            "LOCAL_EMBEDDING_MODEL",
            "BAAI/bge-m3",
        ).strip()
    )
    embedding_device: str = field(
        default_factory=lambda: os.getenv("EMBEDDING_DEVICE", "").strip()
    )
    local_speech_model: str = field(
        default_factory=lambda: os.getenv(
            "LOCAL_SPEECH_MODEL",
            "openai/whisper-small",
        ).strip()
    )
    speech_language: str = field(
        default_factory=lambda: os.getenv("SPEECH_LANGUAGE", "zh").strip()
    )
    embedding_cache_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("HUGGINGFACE_CACHE_DIR", "D:/huggingface_cache")
        )
    )
    preview_timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("PREVIEW_TIMEOUT_SECONDS", "240"))
    )
    cors_origins: list[str] = field(default_factory=lambda: ["*"])

    @property
    def sqlalchemy_database_url(self) -> str:
        return f"sqlite:///{self.auth_database_file.as_posix()}"


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.backup_dir.mkdir(parents=True, exist_ok=True)
settings.embedding_cache_dir.mkdir(parents=True, exist_ok=True)
settings.vector_db_dir.mkdir(parents=True, exist_ok=True)
settings.legacy_user_file.parent.mkdir(parents=True, exist_ok=True)
