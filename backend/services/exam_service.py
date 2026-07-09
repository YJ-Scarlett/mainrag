import json
import re
import uuid
from datetime import datetime

import httpx
from fastapi import HTTPException

from core.config import settings
from services.document_service import get_document
from storage.json_store import store


def _parse_json(content: str) -> list[dict]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.I)
    match = re.search(r"\[[\s\S]*\]", cleaned)
    if match:
        cleaned = match.group(0)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise HTTPException(502, "DeepSeek 返回的习题格式无法解析，请重新生成") from exc
    if not isinstance(value, list):
        raise HTTPException(502, "DeepSeek 未返回习题数组")
    return value


def _normalize_questions(items: list[dict], count: int) -> list[dict]:
    questions = []
    for item in items[:count]:
        options = item.get("options") or []
        if isinstance(options, dict):
            options = [f"{key}. {value}" for key, value in options.items()]
        raw_type = str(item.get("type") or item.get("question_type") or "").lower()
        if options:
            question_type = "choice"
        elif any(key in raw_type for key in ["fill", "blank", "填空"]):
            question_type = "fill"
        elif any(key in raw_type for key in ["solution", "essay", "answer", "解答", "简答"]):
            question_type = "solution"
        else:
            question_type = "solution"
        answer = str(item.get("answer", "")).strip()
        questions.append({
            "id": uuid.uuid4().hex[:10],
            "type": question_type,
            "question": str(item.get("question", "")).strip(),
            "options": options,
            "answer": answer,
            "analysis": str(item.get("analysis", "")).strip(),
            "knowledge_point": str(item.get("knowledge_point", "综合知识")),
            "score": 10,
        })
    if not questions or any(not item["question"] or not item["answer"] for item in questions):
        raise HTTPException(502, "生成的题目不完整，请重新生成")
    return questions


async def generate_exam(document_id: str, chapter: str, title: str, count: int, difficulty: str, question_types: list[str] | None = None) -> dict:
    if not settings.deepseek_api_key:
        raise HTTPException(503, "尚未配置 DEEPSEEK_API_KEY，无法生成习题")
    document = get_document(document_id)
    source = document["content"][:30000]
    type_map = {"choice": "单项选择题", "fill": "填空题", "solution": "解答题"}
    selected_types = [item for item in (question_types or ["choice", "fill", "solution"]) if item in type_map]
    if not selected_types:
        selected_types = ["choice", "fill", "solution"]
    type_text = "、".join(type_map[item] for item in selected_types)
    prompt = f"""根据下面的课程资料生成 {count} 道{difficulty}难度习题，范围为“{chapter}”。
题型范围：{type_text}。请尽量均衡覆盖所选题型。严格返回 JSON 数组，不要输出 Markdown。
每项格式：{{"type":"choice/fill/solution","question":"题干","options":["A. ...","B. ...","C. ...","D. ..."],"answer":"答案或参考答案","analysis":"解析","knowledge_point":"知识点"}}。
单项选择题 type 为 choice，options 返回 4 个选项，answer 返回选项字母。
填空题 type 为 fill，options 返回空数组，题干用“____”标出空缺，answer 返回标准填空答案。
解答题 type 为 solution，options 返回空数组，answer 返回参考答案。题目必须能从资料中得到答案。

课程资料：
{source}"""
    payload = {"model": settings.deepseek_model, "temperature": 0.5, "messages": [{"role": "user", "content": prompt}]}
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{settings.deepseek_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"}, json=payload,
            )
            response.raise_for_status()
            generated = _parse_json(response.json()["choices"][0]["message"]["content"])
    except httpx.HTTPStatusError as exc:
        raise HTTPException(502, f"DeepSeek 生成失败：{exc.response.text[:300]}") from exc
    except (httpx.HTTPError, KeyError, IndexError) as exc:
        raise HTTPException(502, f"DeepSeek 服务异常：{exc}") from exc
    exam = {
        "id": uuid.uuid4().hex[:10], "title": title.strip() or f"{document['name']} · {chapter}练习",
        "document_id": document_id, "document_name": document["name"], "chapter": chapter,
        "difficulty": difficulty, "status": "draft", "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "questions": _normalize_questions(generated, count),
    }
    data = store.load(); data["exams"].insert(0, exam); store.save(data)
    return exam


def list_exams(published_only: bool = False) -> list[dict]:
    exams = store.load()["exams"]
    if published_only:
        exams = [item for item in exams if item["status"] == "published"]
    return exams


def publish_exam(exam_id: str, question_ids: list[str] | None = None) -> dict:
    data = store.load()
    exam = next((item for item in data["exams"] if item["id"] == exam_id), None)
    if not exam: raise HTTPException(404, "习题不存在")
    if question_ids:
        selected = [question for question in exam["questions"] if question["id"] in set(question_ids)]
        if not selected:
            raise HTTPException(400, "请至少选择一道习题发布")
        exam["questions"] = selected
    exam["status"] = "published"; exam["published_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    store.save(data); return exam


def delete_exam(exam_id: str) -> None:
    data = store.load(); remaining = [item for item in data["exams"] if item["id"] != exam_id]
    if len(remaining) == len(data["exams"]): raise HTTPException(404, "习题不存在")
    data["exams"] = remaining; store.save(data)


def submit_exam(exam_id: str, student: str, answers: dict[str, str]) -> dict:
    data = store.load(); exam = next((item for item in data["exams"] if item["id"] == exam_id and item["status"] == "published"), None)
    if not exam: raise HTTPException(404, "已发布习题不存在")
    details, earned, total = [], 0, 0
    for question in exam["questions"]:
        student_answer = str(answers.get(question["id"], "")).strip()
        standard_answer = str(question["answer"]).strip()
        if question.get("type") == "solution":
            correct = bool(student_answer) and (
                student_answer.lower() == standard_answer.lower()
                or standard_answer.lower() in student_answer.lower()
                or student_answer.lower() in standard_answer.lower()
            )
        else:
            correct = student_answer.lower() == standard_answer.lower()
        total += question["score"]
        if correct: earned += question["score"]
        details.append({**question, "student_answer": student_answer, "correct": correct})
    submission = {
        "id": uuid.uuid4().hex[:10], "exam_id": exam_id, "exam_title": exam["title"], "student": student,
        "score": earned, "total": total, "accuracy": round(earned / total * 100) if total else 0,
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"), "details": details,
    }
    data["submissions"] = [item for item in data["submissions"] if not (item["exam_id"] == exam_id and item["student"] == student)]
    data["submissions"].insert(0, submission); store.save(data)
    return submission


def student_submissions(student: str) -> list[dict]:
    return [item for item in store.load()["submissions"] if item["student"] == student]


def wrong_questions(student: str) -> list[dict]:
    result = []
    for submission in student_submissions(student):
        for detail in submission["details"]:
            if not detail["correct"]:
                result.append({**detail, "exam_id": submission["exam_id"], "exam_title": submission["exam_title"], "submitted_at": submission["submitted_at"]})
    return result
