from enum import Enum, unique
from typing import TypedDict, Literal, Protocol, Any

__all__ = ("Task", "TaskStatus", "TypedDictType", "TaskStatusEnum", "TaskRow", "HasId")


@unique
class TaskStatusEnum(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

    @property
    def label(self) -> str:
        return self.value.replace("_", " ").upper()


TaskStatus = Literal["todo", "in_progress", "done"]


class Task(TypedDict):
    id: int
    description: str
    status: TaskStatus
    created_at: str
    updated_at: str


class TaskRow(TypedDict):
    id: int
    description: str
    status: str
    created_at: str
    updated_at: str


class HasId(TypedDict):
    id: int


class TypedDictType(Protocol):
    __annotations__: dict[str, Any]
    __required_keys__: frozenset[str]
    __optional_keys__: frozenset[str]
