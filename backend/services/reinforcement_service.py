import json
import re
import threading
import time
import uuid

import httpx
from fastapi import HTTPException

from core.config import settings
from services.retrieval_service import retrieve


# 巩固练习只保存为临时内存会话，不写入 store.json。
# 后端重启后会话自动失效。
_SESSION_TTL_SECONDS = 30 * 60

_sessions: dict[str, dict] = {}
_session_lock = threading.RLock()


def _cleanup_expired_sessions() -> None:
    """删除超过有效期的临时练习会话。"""

    now = time.monotonic()

    with _session_lock:
        expired_ids = [
            session_id
            for session_id, session in _sessions.items()
            if now - session["created_at"] > _SESSION_TTL_SECONDS
        ]

        for session_id in expired_ids:
            _sessions.pop(session_id, None)


def _parse_json_array(content: str) -> list[dict]:
    """从 DeepSeek 返回内容中提取 JSON 数组。"""

    cleaned = content.strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        cleaned,
        flags=re.I,
    )

    match = re.search(r"\[[\s\S]*\]", cleaned)

    if match:
        cleaned = match.group(0)

    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            502,
            "AI 返回的巩固习题格式无法解析，请重新生成。",
        ) from exc

    if not isinstance(value, list):
        raise HTTPException(
            502,
            "AI 未返回有效的习题数组。",
        )

    return value


def _normalize_questions(
    items: list[dict],
    count: int,
) -> list[dict]:
    """统一 AI 返回的题目结构。"""

    questions: list[dict] = []

    for item in items[:count]:
        question = str(
            item.get("question", "")
        ).strip()

        answer = str(
            item.get("answer", "")
        ).strip()

        analysis = str(
            item.get("analysis", "")
        ).strip()

        options = item.get("options") or []

        if isinstance(options, dict):
            options = [
                f"{key}. {value}"
                for key, value in options.items()
            ]

        if not isinstance(options, list):
            options = []

        options = [
            str(option).strip()
            for option in options
            if str(option).strip()
        ]

        raw_type = str(
            item.get("type", "")
        ).lower()

        # 有选项时统一视为单选题，否则为填空题。
        question_type = (
            "choice"
            if options
            else "fill"
        )

        if "fill" in raw_type or "填空" in raw_type:
            question_type = "fill"

        accepted_answers = item.get(
            "accepted_answers",
            [],
        )

        if isinstance(accepted_answers, str):
            accepted_answers = [accepted_answers]

        if not isinstance(accepted_answers, list):
            accepted_answers = []

        accepted_answers = [
            str(value).strip()
            for value in accepted_answers
            if str(value).strip()
        ]

        if not question or not answer:
            continue

        if question_type == "choice" and len(options) < 2:
            continue

        questions.append({
            "id": uuid.uuid4().hex[:10],
            "type": question_type,
            "question": question,
            "options": options,
            "answer": answer,
            "accepted_answers": accepted_answers,
            "analysis": analysis or "暂无详细解析。",
        })

    if not questions:
        raise HTTPException(
            502,
            "AI 没有生成完整习题，请重新尝试。",
        )

    return questions


def _public_question(question: dict) -> dict:
    """返回给前端的题目，不暴露答案和解析。"""

    return {
        "id": question["id"],
        "type": question["type"],
        "question": question["question"],
        "options": question["options"],
    }


def _normalize_text(value: str) -> str:
    """标准化填空题答案。"""

    text = str(value or "").strip().lower()

    return re.sub(
        r"[\s，。；;、,：:（）()《》“”\"'`]+",
        "",
        text,
    )


def _choice_letter(
    value: str,
    options: list[str],
) -> str:
    """从 A、A.选项文字或完整选项中提取选项字母。"""

    raw = str(value or "").strip()

    match = re.match(
        r"^\s*([A-Da-d])(?:[\s.、:：]|$)",
        raw,
    )

    if match:
        return match.group(1).upper()

    normalized = _normalize_text(raw)

    for index, option in enumerate(options):
        option_letter = chr(ord("A") + index)
        normalized_option = _normalize_text(option)

        option_text = re.sub(
            r"^[A-Da-d][\s.、:：]*",
            "",
            option,
        )

        normalized_option_text = _normalize_text(
            option_text
        )

        if normalized in {
            normalized_option,
            normalized_option_text,
        }:
            return option_letter

    return raw.upper()


def _is_correct(
    question: dict,
    student_answer: str,
) -> bool:
    """判定单选题或填空题答案。"""

    if question["type"] == "choice":
        student_choice = _choice_letter(
            student_answer,
            question["options"],
        )

        standard_choice = _choice_letter(
            question["answer"],
            question["options"],
        )

        return student_choice == standard_choice

    accepted = [
        question["answer"],
        *question.get("accepted_answers", []),
    ]

    normalized_student = _normalize_text(
        student_answer
    )

    normalized_accepted = {
        _normalize_text(value)
        for value in accepted
        if _normalize_text(value)
    }

    return normalized_student in normalized_accepted


async def generate_reinforcement(
    knowledge_point: str,
    count: int = 3,
) -> dict:
    """按知识点检索课程资料并生成专项巩固习题。"""

    knowledge_point = knowledge_point.strip()

    if not knowledge_point:
        raise HTTPException(
            400,
            "知识点不能为空。",
        )

    if not settings.deepseek_api_key:
        raise HTTPException(
            503,
            "尚未配置 DEEPSEEK_API_KEY，无法生成巩固习题。",
        )

    references = await retrieve(
        f"知识点：{knowledge_point}",
        top_k=6,
    )

    if not references:
        raise HTTPException(
            404,
            f"知识库中没有找到与“{knowledge_point}”相关的课程内容。",
        )

    context_parts = []

    for index, reference in enumerate(references, start=1):
        document = reference.get(
            "document",
            "课程资料",
        )

        content = reference.get(
            "content",
            "",
        )

        context_parts.append(
            f"[资料{index}：{document}]\n{content}"
        )

    # 防止上下文过长。
    context = "\n\n".join(context_parts)[:24000]

    prompt = f"""
请严格根据下面的课程资料，为知识点“{knowledge_point}”生成 {count} 道专项巩固习题。

要求：
1. 只生成单项选择题和填空题，不生成简答题或解答题。
2. 题目必须直接围绕知识点“{knowledge_point}”。
3. 优先生成 2 道单选题和 1 道填空题。
4. 单选题必须有 4 个选项，answer 返回正确选项字母。
5. 填空题 answer 返回标准答案；如存在同义答案，可使用 accepted_answers 数组。
6. 每道题必须提供清晰解析。
7. 不得使用资料之外的知识。
8. 严格返回 JSON 数组，不要输出 Markdown 或其他文字。

每项格式：
{{
  "type": "choice/fill",
  "question": "题干",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "answer": "A 或标准答案",
  "accepted_answers": ["可接受的同义答案"],
  "analysis": "答案解析"
}}

课程资料：
{context}
""".strip()

    payload = {
        "model": settings.deepseek_model,
        "temperature": 0.2,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是课程专项练习生成器。"
                    "只能依据用户提供的课程资料生成题目，"
                    "必须严格输出可解析的 JSON 数组。"
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    }

    try:
        async with httpx.AsyncClient(
            timeout=90,
        ) as client:
            response = await client.post(
                f"{settings.deepseek_base_url}/chat/completions",
                headers={
                    "Authorization":
                        f"Bearer {settings.deepseek_api_key}"
                },
                json=payload,
            )

            response.raise_for_status()

            content = response.json()[
                "choices"
            ][0]["message"]["content"]

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            502,
            f"DeepSeek 调用失败：{exc.response.text[:300]}",
        ) from exc

    except (
        httpx.HTTPError,
        KeyError,
        IndexError,
    ) as exc:
        raise HTTPException(
            502,
            f"巩固习题生成服务异常：{exc}",
        ) from exc

    questions = _normalize_questions(
        _parse_json_array(content),
        count,
    )

    session_id = uuid.uuid4().hex

    session = {
        "id": session_id,
        "knowledge_point": knowledge_point,
        "questions": questions,
        "created_at": time.monotonic(),
    }

    _cleanup_expired_sessions()

    with _session_lock:
        _sessions[session_id] = session

    return {
        "session_id": session_id,
        "knowledge_point": knowledge_point,
        "questions": [
            _public_question(question)
            for question in questions
        ],
    }


def check_reinforcement_answer(
    session_id: str,
    question_id: str,
    answer: str,
) -> dict:
    """检查一道巩固习题答案。"""

    _cleanup_expired_sessions()

    with _session_lock:
        session = _sessions.get(session_id)

    if not session:
        raise HTTPException(
            404,
            "巩固练习已过期，请重新生成。",
        )

    question = next(
        (
            item
            for item in session["questions"]
            if item["id"] == question_id
        ),
        None,
    )

    if not question:
        raise HTTPException(
            404,
            "当前题目不存在。",
        )

    student_answer = str(answer or "").strip()

    if not student_answer:
        raise HTTPException(
            400,
            "请先输入或选择答案。",
        )

    correct = _is_correct(
        question,
        student_answer,
    )

    return {
        "question_id": question_id,
        "correct": correct,
        "student_answer": student_answer,
        "correct_answer": question["answer"],
        "analysis": question["analysis"],
    }