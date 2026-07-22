from sqlalchemy.orm import Session

from db.models import User
from services.classroom_service import (
    list_class_students,
    list_teacher_classrooms,
    require_class_teacher,
)
from services.identity_service import user_aliases
from storage.json_store import store


def _matches_identity(
    item: dict,
    *,
    student: str | None = None,
    student_id: str | None = None,
    aliases: set[str] | None = None,
    id_fields: tuple[str, ...] = ("student_id", "user_id"),
) -> bool:
    """
    匹配单个学生。

    这里恢复原来的单学生匹配逻辑，不再接收 student_ids。
    学生端和单个学生概览都使用这个函数。
    """
    if student_id:
        found_identity_field = False

        for field in id_fields:
            value = item.get(field)

            if value:
                found_identity_field = True

                if str(value).strip() == student_id:
                    return True

        # 记录已经存在稳定 ID，但与当前学生不一致时，
        # 不能继续通过姓名误匹配到其他学生。
        if found_identity_field:
            return False

    if aliases:
        legacy_value = str(item.get("student", "")).strip()
        return legacy_value in aliases

    if student:
        return str(item.get("student", "")).strip() == student

    return True


def build_analysis(
    student: str | None = None,
    *,
    student_id: str | None = None,
    aliases: set[str] | None = None,
) -> dict:
    """
    生成单个学生的学情。

    不包含任何班级筛选逻辑，避免教师端改动影响学生端。
    """
    data = store.load()

    activities = [
        item
        for item in data.get("activities", [])
        if _matches_identity(
            item,
            student=student,
            student_id=student_id,
            aliases=aliases,
            id_fields=("student_id",),
        )
    ]

    topics: dict[str, list[int]] = {}

    for item in activities:
        topic = str(item.get("topic") or "综合知识").strip()
        score = int(item.get("score") or 0)
        topics.setdefault(topic, []).append(score)

    average = (
        round(
            sum(int(item.get("score") or 0) for item in activities)
            / len(activities)
        )
        if activities
        else 0
    )

    questions = [
        item
        for item in data.get("questions", [])
        if _matches_identity(
            item,
            student=student,
            student_id=student_id,
            aliases=aliases,
            id_fields=("user_id", "student_id"),
        )
    ]

    submissions = [
        item
        for item in data.get("submissions", [])
        if _matches_identity(
            item,
            student=student,
            student_id=student_id,
            aliases=aliases,
            id_fields=("student_id",),
        )
        and item.get("status", "graded") == "graded"
    ]

    exam_topics: dict[str, list[int]] = {}

    for submission in submissions:
        for detail in submission.get("details", []):
            if detail.get("grading_status", "graded") != "graded":
                continue

            knowledge_points = detail.get("knowledge_points")

            if not knowledge_points:
                knowledge_points = [
                    detail.get("knowledge_point", "综合知识")
                ]

            if isinstance(knowledge_points, str):
                knowledge_points = [knowledge_points]

            clean_points = {
                str(point).strip()
                for point in knowledge_points
                if str(point).strip()
            }

            score = 100 if detail.get("correct") else 0

            for topic in clean_points:
                exam_topics.setdefault(topic, []).append(score)

    for topic, scores in exam_topics.items():
        topics.setdefault(topic, []).extend(scores)

    mastery = sorted(
        (
            {
                "topic": topic,
                "score": round(sum(scores) / len(scores)),
            }
            for topic, scores in topics.items()
            if scores
        ),
        key=lambda item: item["score"],
    )

    graded_accuracies = [
        item.get("accuracy")
        for item in submissions
        if item.get("accuracy") is not None
    ]

    if graded_accuracies:
        average = round(
            sum(float(value) for value in graded_accuracies)
            / len(graded_accuracies)
        )

    activity_trend = [
        {
            "date": item.get("at", ""),
            "score": int(item.get("score") or 0),
            "topic": item.get("topic") or "综合知识",
        }
        for item in activities
    ]

    submission_trend = [
        {
            "date": str(item.get("submitted_at") or "")[:10],
            "score": float(item.get("accuracy") or 0),
            "topic": item.get("exam_title") or "练习",
        }
        for item in submissions
        if item.get("accuracy") is not None
    ]

    return {
        "summary": {
            "average": average,
            "activities": len(activities) + len(submissions),
            "questions": len(questions),
            # 课程资料仍然是全平台共享资源。
            "documents": len(data.get("documents", [])),
            "exams": len(submissions),
        },
        "mastery": mastery,
        "trend": activity_trend + submission_trend,
        "suggestion": (
            f"优先复习“{mastery[0]['topic']}”，"
            "结合知识库问答完成概念辨析。"
            if mastery
            else "暂无足够学习记录。"
        ),
    }


def build_user_analysis(user: User) -> dict:
    """
    学生端只分析当前登录学生。
    """
    return build_analysis(
        student_id=user.id,
        aliases=user_aliases(user),
    )


def _member_aliases(member: dict) -> set[str]:
    return {
        str(value).strip()
        for value in (
            member.get("id"),
            member.get("username"),
            member.get("name"),
        )
        if str(value or "").strip()
    }


def _empty_class_analysis(
    *,
    classroom: dict | None,
    document_count: int,
) -> dict:
    return {
        "summary": {
            "average": 0,
            "activities": 0,
            "questions": 0,
            "documents": document_count,
            "exams": 0,
        },
        "mastery": [],
        "trend": [],
        "students": [],
        "suggestion": "暂无足够学习记录。",
        "classroom": classroom,
    }


def build_class_analysis(
    db: Session,
    teacher: User,
    *,
    class_id: str | None = None,
) -> dict:
    """
    只聚合当前班级学生的学情。

    不修改 build_analysis() 的学生身份匹配逻辑，
    而是逐个调用稳定的单学生分析，再汇总为班级分析。
    """
    data = store.load()
    document_count = len(data.get("documents", []))

    # 教师首页仍可能不传 class_id。
    # 此时使用该教师班级列表中的第一个班级。
    if not class_id:
        classrooms = list_teacher_classrooms(db, teacher)

        if not classrooms:
            return _empty_class_analysis(
                classroom=None,
                document_count=document_count,
            )

        class_id = classrooms[0]["id"]

    # 验证当前教师属于该班级。
    classroom_model, _ = require_class_teacher(
        db,
        class_id,
        teacher,
    )

    classroom_public = {
        "id": classroom_model.id,
        "name": classroom_model.name,
    }

    # 只获取当前班级中的有效学生。
    members = list_class_students(
        db,
        class_id,
        teacher,
    )

    if not members:
        return _empty_class_analysis(
            classroom=classroom_public,
            document_count=document_count,
        )

    students: list[dict] = []
    combined_mastery: dict[str, list[float]] = {}
    combined_trend: list[dict] = []

    total_activities = 0
    total_questions = 0
    total_exams = 0

    weighted_average_total = 0.0
    weighted_average_count = 0

    for member in members:
        member_id = str(member.get("id") or "").strip()

        if not member_id:
            continue

        analysis = build_analysis(
            student_id=member_id,
            aliases=_member_aliases(member),
        )

        summary = analysis.get("summary", {})
        activity_count = int(summary.get("activities") or 0)
        student_average = float(summary.get("average") or 0)

        total_activities += activity_count
        total_questions += int(summary.get("questions") or 0)
        total_exams += int(summary.get("exams") or 0)

        # 有学习活动的学生才参与班级平均分计算。
        if activity_count > 0:
            weighted_average_total += (
                student_average * activity_count
            )
            weighted_average_count += activity_count

        for item in analysis.get("mastery", []):
            topic = str(item.get("topic") or "").strip()

            if not topic:
                continue

            combined_mastery.setdefault(topic, []).append(
                float(item.get("score") or 0)
            )

        combined_trend.extend(analysis.get("trend", []))

        students.append(
            {
                "id": member_id,
                "username": member.get("username"),
                "name": (
                    member.get("name")
                    or member.get("username")
                    or "学生"
                ),
                "average": round(student_average),
                "activities": activity_count,
                "questions": int(summary.get("questions") or 0),
                "documents": document_count,
                "exams": int(summary.get("exams") or 0),
            }
        )

    mastery = sorted(
        (
            {
                "topic": topic,
                "score": round(sum(scores) / len(scores)),
            }
            for topic, scores in combined_mastery.items()
            if scores
        ),
        key=lambda item: item["score"],
    )

    class_average = (
        round(weighted_average_total / weighted_average_count)
        if weighted_average_count
        else 0
    )

    combined_trend.sort(
        key=lambda item: str(item.get("date") or "")
    )

    students.sort(
        key=lambda item: str(item.get("name") or "")
    )

    return {
        "summary": {
            "average": class_average,
            "activities": total_activities,
            "questions": total_questions,
            "documents": document_count,
            "exams": total_exams,
        },
        "mastery": mastery,
        "trend": combined_trend,
        "students": students,
        "suggestion": (
            f"建议优先巩固“{mastery[0]['topic']}”，"
            "并关注掌握度较低的学生。"
            if mastery
            else "暂无足够学习记录。"
        ),
        "classroom": classroom_public,
    }