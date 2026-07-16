import json
import re
import uuid
from copy import deepcopy
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

def _normalize_knowledge_points(item: dict) -> list[str]:
    raw_points = item.get("knowledge_points")

    # 兼容 AI 或旧数据仍返回单个 knowledge_point
    if raw_points is None:
        raw_points = item.get("knowledge_point", "综合知识")

    if isinstance(raw_points, str):
        raw_points = [raw_points]

    if not isinstance(raw_points, list):
        raw_points = ["综合知识"]

    result = []
    for point in raw_points:
        point = str(point).strip()
        if point and point not in result:
            result.append(point)

    return result or ["综合知识"]

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
        knowledge_points = _normalize_knowledge_points(item)
        questions.append({
            "id": uuid.uuid4().hex[:10],
            "type": question_type,
            "question": str(item.get("question", "")).strip(),
            "options": options,
            "answer": answer,
            "analysis": str(item.get("analysis", "")).strip(),
            "knowledge_points": knowledge_points,

# 暂时保留旧字段，避免其他功能立即报错
"knowledge_point": knowledge_points[0],
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
每项格式：{{"type":"choice/fill/solution","question":"题干","options":["A. ...","B. ...","C. ...","D. ..."],"answer":"答案或参考答案","analysis":"解析","knowledge_points":["知识点1","知识点2"]}}。
每道题的 knowledge_points 必须是 JSON 字符串数组，包含 1 到 3 个与该题直接相关的知识点，不要返回笼统或重复的知识点。
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


async def _grade_solutions_with_ai(questions: list[dict], answers: dict[str, str]) -> dict[str, dict]:
    if not questions:
        return {}
    if not settings.deepseek_api_key:
        raise HTTPException(503, "尚未配置 DEEPSEEK_API_KEY，无法使用 AI 批改解答题")
    grading_items = [
        {
            "id": question["id"],
            "question": question["question"],
            "reference_answer": question["answer"],
            "student_answer": str(answers.get(question["id"], "")).strip(),
            "max_score": question["score"],
        }
        for question in questions
    ]
    prompt = f"""你是一名严谨的课程教师。请依据题目和参考答案批改学生的解答题。
按要点给分，空白答案得 0 分；分数不能超过 max_score。请为每题给出简短、具体的中文评语。
严格返回 JSON 数组，不要输出 Markdown。每项格式：
{{"id":"题目ID","score":数字,"comment":"评分理由和改进建议"}}

待批改内容：
{json.dumps(grading_items, ensure_ascii=False)}"""
    payload = {
        "model": settings.deepseek_model,
        "temperature": 0.1,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{settings.deepseek_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
                json=payload,
            )
            response.raise_for_status()
            rows = _parse_json(response.json()["choices"][0]["message"]["content"])
    except httpx.HTTPStatusError as exc:
        raise HTTPException(502, f"DeepSeek 批改失败：{exc.response.text[:300]}") from exc
    except (httpx.HTTPError, KeyError, IndexError) as exc:
        raise HTTPException(502, f"DeepSeek 批改服务异常：{exc}") from exc

    maximums = {item["id"]: float(item["score"]) for item in questions}
    result = {}
    for row in rows:
        question_id = str(row.get("id", ""))
        if question_id not in maximums:
            continue
        try:
            score = float(row.get("score", 0))
        except (TypeError, ValueError):
            score = 0
        result[question_id] = {
            "score": max(0, min(maximums[question_id], score)),
            "comment": str(row.get("comment", "AI 已完成评分")),
        }
    for question in questions:
        result.setdefault(question["id"], {"score": 0, "comment": "AI 未返回有效评分，请联系教师复核"})
    return result


async def submit_exam(exam_id: str, student: str, answers: dict[str, str], solution_grading: str = "ai") -> dict:
    data = store.load(); exam = next((item for item in data["exams"] if item["id"] == exam_id and item["status"] == "published"), None)
    if not exam: raise HTTPException(404, "已发布习题不存在")
    if solution_grading not in {"ai", "teacher"}:
        raise HTTPException(400, "解答题批改方式只能选择 ai 或 teacher")
    solution_questions = [question for question in exam["questions"] if question.get("type") == "solution"]
    ai_grades = await _grade_solutions_with_ai(solution_questions, answers) if solution_grading == "ai" else {}
    details, earned, total = [], 0, 0
    for question in exam["questions"]:
        student_answer = str(answers.get(question["id"], "")).strip()
        standard_answer = str(question["answer"]).strip()
        if question.get("type") == "solution":
            if solution_grading == "ai":
                grade = ai_grades[question["id"]]
                awarded = grade["score"]
                feedback = grade["comment"]
                grading_status = "graded"
                correct = awarded >= float(question["score"]) * 0.6
            else:
                awarded = None
                feedback = "已提交教师批改"
                grading_status = "pending"
                correct = None
        else:
            correct = student_answer.lower() == standard_answer.lower()
            awarded = question["score"] if correct else 0
            feedback = question.get("analysis", "")
            grading_status = "graded"
        total += question["score"]
        if awarded is not None:
            earned += awarded
        details.append({
            **question,
            "student_answer": student_answer,
            "correct": correct,
            "score_awarded": awarded,
            "feedback": feedback,
            "grading_status": grading_status,
            "grading_method": solution_grading if question.get("type") == "solution" else "auto",
        })
    pending_teacher = solution_grading == "teacher" and bool(solution_questions)
    submission = {
        "id": uuid.uuid4().hex[:10], "exam_id": exam_id, "exam_title": exam["title"], "student": student,
        "score": round(earned, 1), "total": total,
        "accuracy": None if pending_teacher else (round(earned / total * 100) if total else 0),
        "status": "pending_teacher" if pending_teacher else "graded",
        "solution_grading": solution_grading,
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"), "details": details,
    }
    data["submissions"] = [item for item in data["submissions"] if not (item["exam_id"] == exam_id and item["student"] == student)]
    data["submissions"].insert(0, submission); store.save(data)
    return submission


def student_submissions(student: str) -> list[dict]:
    return [student_submission_view(item) for item in store.load()["submissions"] if item["student"] == student]


def student_submission_view(submission: dict) -> dict:
    result = deepcopy(submission)
    if result.get("status") == "pending_teacher":
        for detail in result.get("details", []):
            if detail.get("type") == "solution" and detail.get("grading_status") == "pending":
                detail.pop("answer", None)
                detail.pop("analysis", None)
    return result


def list_submissions(status: str | None = None) -> list[dict]:
    items = store.load()["submissions"]
    if status:
        items = [item for item in items if item.get("status", "graded") == status]
    return items


def grade_submission(submission_id: str, grades: dict[str, dict], overall_comment: str = "") -> dict:
    data = store.load()
    submission = next((item for item in data["submissions"] if item["id"] == submission_id), None)
    if not submission:
        raise HTTPException(404, "提交记录不存在")
    if submission.get("status") != "pending_teacher":
        raise HTTPException(400, "该试卷不处于待教师批改状态")

    pending_ids = {
        detail["id"] for detail in submission["details"]
        if detail.get("type") == "solution" and detail.get("grading_status") == "pending"
    }
    if not pending_ids or not pending_ids.issubset(grades.keys()):
        raise HTTPException(400, "请为全部待批改解答题填写分数")

    for detail in submission["details"]:
        if detail["id"] not in pending_ids:
            continue
        grade = grades[detail["id"]]
        maximum = float(detail["score"])
        score = float(grade.get("score", 0))
        if score < 0 or score > maximum:
            raise HTTPException(400, f"题目“{detail['question'][:20]}”的分数应在 0 到 {maximum:g} 之间")
        detail["score_awarded"] = score
        detail["feedback"] = str(grade.get("comment", "")).strip()
        detail["teacher_comment"] = detail["feedback"]
        detail["grading_status"] = "graded"
        detail["grading_method"] = "teacher"
        detail["correct"] = score >= maximum * 0.6

    earned = sum(float(detail.get("score_awarded") or 0) for detail in submission["details"])
    submission["score"] = round(earned, 1)
    submission["accuracy"] = round(earned / submission["total"] * 100) if submission["total"] else 0
    submission["status"] = "graded"
    submission["overall_comment"] = overall_comment.strip()
    submission["graded_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    store.save(data)
    return submission


def wrong_questions(student: str) -> list[dict]:
    result = []
    for submission in student_submissions(student):
        for detail in submission["details"]:
            if detail.get("grading_status", "graded") == "graded" and detail.get("correct") is False:
                result.append({**detail, "exam_id": submission["exam_id"], "exam_title": submission["exam_title"], "submitted_at": submission["submitted_at"]})
    return result
