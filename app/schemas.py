from typing import TypedDict, Literal, Protocol, Any, NamedTuple

__all__ = (
    "Task",
    "TaskStatus",
    "TypedDictType",
    "TaskRow",
    "HasId",
    "LoadTasksOk",
    "LoadTasksErr",
)


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


class LoadTasksOk(NamedTuple):
    success: Literal[True]
    value: list[Task]


class LoadTasksErr(NamedTuple):
    success: Literal[False]
    msg: str


class HasId(TypedDict):
    id: int


class TypedDictType(Protocol):
    __annotations__: dict[str, Any]
    __required_keys__: frozenset[str]
    __optional_keys__: frozenset[str]
