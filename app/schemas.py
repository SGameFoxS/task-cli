from enum import StrEnum, unique
from typing import TypedDict, Literal, Protocol, Any

__all__ = ("Task", "TaskStatus", "TypedDictType", "TaskStatusEnum")


@unique
class TaskStatusEnum(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


TaskStatus = Literal["todo", "in_progress", "done"]


class Task(TypedDict):
    id: int
    description: str
    status: TaskStatus
    created_at: str
    updated_at: str


class TypedDictType(Protocol):
    __annotations__: dict[str, Any]
    __required_keys__: frozenset[str]
    __optional_keys__: frozenset[str]
