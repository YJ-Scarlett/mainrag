from db.models import User
from services.identity_service import record_belongs_to_user, user_aliases
from storage.json_store import store


def _matches_identity(
    item: dict,
    *,
    student: str | None = None,
    student_id: str | None = None,
    aliases: set[str] | None = None,
    id_fields: tuple[str, ...] = ("student_id", "user_id"),
) -> bool:
    if student_id:
        for field in id_fields:
            if item.get(field):
                return str(item.get(field)) == student_id
    if aliases:
        return str(item.get("student", "")) in aliases
    if student:
        return str(item.get("student", "")) == student
    return True


def build_analysis(
    student: str | None = None,
    *,
    student_id: str | None = None,
    aliases: set[str] | None = None,
) -> dict:
    data = store.load()
    activities = [
        item
        for item in data["activities"]
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
        topics.setdefault(item["topic"], []).append(item["score"])

    average = (
        round(sum(item["score"] for item in activities) / len(activities))
        if activities
        else 0
    )

    questions = [
        item
        for item in data["questions"]
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
        for item in data["submissions"]
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
        for detail in submission["details"]:
            if detail.get("grading_status", "graded") != "graded":
                continue

            knowledge_points = detail.get("knowledge_points")
            if not knowledge_points:
                knowledge_points = [detail.get("knowledge_point", "综合知识")]
            if isinstance(knowledge_points, str):
                knowledge_points = [knowledge_points]

            knowledge_points = {
                str(point).strip()
                for point in knowledge_points
                if str(point).strip()
            }
            score = 100 if detail.get("correct") else 0
            for topic in knowledge_points:
                exam_topics.setdefault(topic, []).append(score)

    for topic, scores in exam_topics.items():
        topics.setdefault(topic, []).extend(scores)

    mastery = sorted(
        (
            {"topic": topic, "score": round(sum(scores) / len(scores))}
            for topic, scores in topics.items()
        ),
        key=lambda item: item["score"],
    )

    graded_accuracies = [
        item.get("accuracy")
        for item in submissions
        if item.get("accuracy") is not None
    ]
    if graded_accuracies:
        average = round(sum(graded_accuracies) / len(graded_accuracies))

    return {
        "summary": {
            "average": average,
            "activities": len(activities) + len(submissions),
            "questions": len(questions),
            "documents": len(data["documents"]),
            "exams": len(submissions),
        },
        "mastery": mastery,
        "trend": (
            [
                {
                    "date": item["at"],
                    "score": item["score"],
                    "topic": item["topic"],
                }
                for item in activities
            ]
            + [
                {
                    "date": item["submitted_at"][:10],
                    "score": item["accuracy"],
                    "topic": item["exam_title"],
                }
                for item in submissions
                if item.get("accuracy") is not None
            ]
        ),
        "suggestion": (
            f"优先复习“{mastery[0]['topic']}”，结合知识库问答完成概念辨析。"
            if mastery
            else "暂无足够学习记录。"
        ),
    }


def build_user_analysis(user: User) -> dict:
    return build_analysis(
        student_id=user.id,
        aliases=user_aliases(user),
    )


def build_class_analysis() -> dict:
    # 第一阶段只完成真实身份鉴权；班级过滤会在第二、三阶段接入。
    payload = build_analysis()
    data = store.load()

    identities: dict[str, dict] = {}
    for item in [*data["activities"], *data["submissions"]]:
        key = str(item.get("student_id") or item.get("student") or "").strip()
        if not key:
            continue
        identities.setdefault(
            key,
            {
                "student_id": item.get("student_id"),
                "legacy": item.get("student"),
                "name": item.get("student_name") or item.get("student") or key,
            },
        )

    students = []
    for identity in sorted(identities.values(), key=lambda item: str(item["name"])):
        summary = build_analysis(
            identity.get("legacy"),
            student_id=identity.get("student_id"),
            aliases={str(identity.get("legacy") or "")},
        )["summary"]
        students.append(
            {
                "id": identity.get("student_id"),
                "name": identity["name"],
                **summary,
            }
        )

    payload["students"] = students
    return payload
