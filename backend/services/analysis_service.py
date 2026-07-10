from storage.json_store import store


def build_analysis(student: str | None = None) -> dict:
    data = store.load()
    activities = [item for item in data["activities"] if not student or item["student"] == student]
    topics: dict[str, list[int]] = {}
    for item in activities:
        topics.setdefault(item["topic"], []).append(item["score"])
    average = round(sum(item["score"] for item in activities) / len(activities)) if activities else 0
    questions = [item for item in data["questions"] if not student or item["student"] == student]
    submissions = [
        item for item in data["submissions"]
        if (not student or item["student"] == student) and item.get("status", "graded") == "graded"
    ]
    exam_topics: dict[str, list[int]] = {}
    for submission in submissions:
        for detail in submission["details"]:
            if detail.get("grading_status", "graded") != "graded":
                continue
            exam_topics.setdefault(detail["knowledge_point"], []).append(100 if detail["correct"] else 0)
    for topic, scores in exam_topics.items():
        topics.setdefault(topic, []).extend(scores)
    mastery = sorted(
        ({"topic": topic, "score": round(sum(scores) / len(scores))} for topic, scores in topics.items()),
        key=lambda item: item["score"],
    )
    if submissions:
        average = round(sum(item["accuracy"] for item in submissions) / len(submissions))
    return {
        "summary": {"average": average, "activities": len(activities) + len(submissions), "questions": len(questions), "documents": len(data["documents"]), "exams": len(submissions)},
        "mastery": mastery,
        "trend": ([{"date": item["at"], "score": item["score"], "topic": item["topic"]} for item in activities] + [{"date": item["submitted_at"][:10], "score": item["accuracy"], "topic": item["exam_title"]} for item in submissions]),
        "suggestion": f"优先复习“{mastery[0]['topic']}”，结合知识库问答完成概念辨析。" if mastery else "暂无足够学习记录。",
    }


def build_class_analysis() -> dict:
    payload = build_analysis()
    data = store.load()
    students = sorted({item["student"] for item in data["activities"]} | {item["student"] for item in data["submissions"]})
    payload["students"] = [{"name": name, **build_analysis(name)["summary"]} for name in students]
    return payload
