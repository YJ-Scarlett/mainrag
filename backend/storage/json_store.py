import json
import shutil
import sqlite3
import threading
from copy import deepcopy

from core.config import settings

SEED_DATA = {
    "documents": [
        {"id": "doc-network", "name": "计算机网络基础", "type": "课程讲义", "size": 18.2, "created_at": "2026-07-01 09:20", "content": "计算机网络采用分层体系结构。OSI参考模型包含物理层、数据链路层、网络层、传输层、会话层、表示层和应用层。TCP/IP体系通常分为网络接口层、网际层、传输层和应用层。TCP是一种面向连接、可靠的字节流传输协议，通过序号、确认、重传和滑动窗口保证可靠性。UDP无连接，首部开销小，适合实时音视频和DNS查询。IP协议负责寻址和路由，IPv4地址为32位，IPv6地址为128位。路由器工作在网络层，根据路由表转发分组。"},
        {"id": "doc-http", "name": "HTTP 与 Web 应用", "type": "实验资料", "size": 8.6, "created_at": "2026-07-02 14:10", "content": "HTTP是应用层协议，采用请求响应模型。常见方法包括GET、POST、PUT和DELETE。状态码200表示成功，404表示资源不存在，500表示服务器内部错误。HTTPS在HTTP和TCP之间引入TLS，提供加密、身份认证和完整性保护。Cookie保存在客户端，Session通常保存在服务器端。HTTP/2支持多路复用和首部压缩，HTTP/3基于QUIC。"},
        {"id": "doc-db", "name": "数据库系统概论", "type": "课程讲义", "size": 12.4, "created_at": "2026-07-03 10:30", "content": "关系数据库以二维表组织数据。主键唯一标识元组，外键用于维护参照完整性。SQL包括数据定义、数据查询、数据操纵和数据控制。事务具有ACID特性：原子性、一致性、隔离性和持久性。索引可以提高查询速度，但会增加存储和写入成本。规范化用于减少数据冗余，常见范式有第一范式、第二范式和第三范式。"},
    ],
    "activities": [
        {"student": "student", "topic": "TCP可靠传输", "score": 72, "at": "2026-07-01"},
        {"student": "student", "topic": "HTTP状态码", "score": 86, "at": "2026-07-02"},
        {"student": "student", "topic": "数据库事务", "score": 78, "at": "2026-07-03"},
    ],
    "questions": [],
    "chat_history": [],
    "exams": [],
    "submissions": [],
}


class SQLiteStore:
    def __init__(self):
        self.path = settings.business_database_file
        self.legacy_path = settings.database_file
        self.lock = threading.RLock()
        self._ensure_schema()
        self._migrate_legacy_if_needed()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS app_store_items (
                    collection TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (collection, item_id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_app_store_items_collection_position
                ON app_store_items (collection, position)
                """
            )

    def _has_business_rows(self) -> bool:
        with self._connect() as connection:
            count = connection.execute("SELECT COUNT(*) FROM app_store_items").fetchone()[0]
        return count > 0

    def _load_legacy_data(self) -> dict:
        if not self.legacy_path.exists():
            return deepcopy(SEED_DATA)
        try:
            data = json.loads(self.legacy_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return deepcopy(SEED_DATA)
        for key, value in SEED_DATA.items():
            data.setdefault(key, deepcopy(value))
        return data

    def _backup_legacy_once(self) -> None:
        if not self.legacy_path.exists():
            return
        backup_path = settings.backup_dir / "store.before_sqlite.json"
        if not backup_path.exists():
            shutil.copy2(self.legacy_path, backup_path)

    def _migrate_legacy_if_needed(self) -> None:
        with self.lock:
            if self._has_business_rows():
                return
            data = self._load_legacy_data()
            self._replace_all(data)
            self._backup_legacy_once()

    def _collections(self, data: dict) -> list[str]:
        names = list(SEED_DATA.keys())
        for name in data:
            if name not in names:
                names.append(name)
        return names

    def _item_id(self, collection: str, index: int, item: object) -> str:
        if isinstance(item, dict) and item.get("id"):
            return str(item["id"])
        return f"{collection}_{index:08d}"

    def _replace_all(self, data: dict) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN")
            connection.execute("DELETE FROM app_store_items")
            for collection in self._collections(data):
                items = data.get(collection, [])
                if not isinstance(items, list):
                    items = []
                for index, item in enumerate(items):
                    connection.execute(
                        """
                        INSERT INTO app_store_items (collection, item_id, position, payload)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            collection,
                            self._item_id(collection, index, item),
                            index,
                            json.dumps(item, ensure_ascii=False, separators=(",", ":")),
                        ),
                    )

    def load(self) -> dict:
        with self.lock:
            self._migrate_legacy_if_needed()
            data: dict[str, list] = {key: [] for key in SEED_DATA}
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT collection, payload
                    FROM app_store_items
                    ORDER BY collection, position
                    """
                ).fetchall()
            for row in rows:
                data.setdefault(row["collection"], []).append(json.loads(row["payload"]))
            return data

    def save(self, data: dict) -> None:
        with self.lock:
            self._replace_all(data)


JsonStore = SQLiteStore
store = SQLiteStore()
