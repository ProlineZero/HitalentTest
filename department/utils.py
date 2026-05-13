from __future__ import annotations

from department.models import Department


def trim_non_empty(value: str, field_label: str, *, max_len: int = 200) -> str:
    cleaned = (value or '').strip()
    if not cleaned:
        raise ValueError(f'{field_label} не может быть пустым')
    if len(cleaned) > max_len:
        raise ValueError(f'{field_label}: длина не более {max_len} символов')
    return cleaned


def would_create_cycle(moving_department_id: int, new_parent_id: int | None) -> bool:
    if new_parent_id is None:
        return False
    if new_parent_id == moving_department_id:
        return True
    current_id: int | None = new_parent_id
    seen: set[int] = set()
    while current_id is not None:
        if current_id == moving_department_id:
            return True
        if current_id in seen:
            return True
        seen.add(current_id)
        current_id = (
            Department.objects.filter(pk=current_id)
            .values_list('parent_id', flat=True)
            .first()
        )
    return False
