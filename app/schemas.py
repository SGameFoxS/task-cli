from typing import TypedDict, Literal, Protocol

__all__ = ("Task", "TaskStatus", "TypedDictType")

TaskStatus = Literal["todo", "in_progress", "done"]


class Task(TypedDict):
    id: int
    description: str
    status: TaskStatus
    created_at: str
    updated_at: str


class TypedDictType(Protocol):
    __annotations__: dict[str, object]
    __required_keys__: frozenset[str]
    __optional_keys__: frozenset[str]
