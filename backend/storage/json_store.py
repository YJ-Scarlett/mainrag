import json
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
        {"student": "张同学", "topic": "TCP可靠传输", "score": 72, "at": "2026-07-01"},
        {"student": "张同学", "topic": "HTTP状态码", "score": 86, "at": "2026-07-02"},
        {"student": "张同学", "topic": "数据库事务", "score": 78, "at": "2026-07-03"},
        {"student": "李同学", "topic": "TCP可靠传输", "score": 91, "at": "2026-07-02"},
        {"student": "王同学", "topic": "HTTP状态码", "score": 64, "at": "2026-07-03"},
    ],
    "questions": [],
    "chat_history": [],
    "exams": [],
    "submissions": [],
}


class JsonStore:
    def __init__(self):
        self.path = settings.database_file
        self.lock = threading.RLock()

    def load(self) -> dict:
        with self.lock:
            if not self.path.exists():
                self.save(deepcopy(SEED_DATA))
            data = json.loads(self.path.read_text(encoding="utf-8"))
            data.setdefault("exams", [])
            data.setdefault("submissions", [])
            data.setdefault("questions", [])
            data.setdefault("chat_history", [])
            return data

    def save(self, data: dict) -> None:
        with self.lock:
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(self.path)


store = JsonStore()
