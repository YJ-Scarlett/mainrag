from db.models import User


def user_aliases(user: User) -> set[str]:
    return {str(value) for value in (user.id, user.username, user.name) if value}


def record_belongs_to_user(
    item: dict,
    user: User,
    *,
    id_fields: tuple[str, ...] = ("user_id", "student_id"),
    legacy_field: str = "student",
) -> bool:
    for field in id_fields:
        value = item.get(field)
        if value:
            return str(value) == user.id
    return str(item.get(legacy_field, "")) in user_aliases(user)


def user_legacy_label(user: User) -> str:
    # 旧 store.json 继续保留 student 字段，使用 username 比显示姓名更稳定。
    return user.username
