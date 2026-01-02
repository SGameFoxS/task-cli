from typing import TypedDict, Literal, Protocol, Any, NamedTuple, Final

__all__ = (
    "Task",
    "TaskStatus",
    "TypedDictType",
    "TaskRow",
    "HasId",
    "LoadTasksOk",
    "LoadTasksErr",
)

# Sentinel: used in runtime schema validation to mean "ISO 8601 datetime string"
ISO_DATETIME = object()

type TaskStatus = Literal["todo", "in_progress", "done"]

TASK_STATUS: Final[tuple[str, ...]] = "todo", "in_progress", "done"

TASK_REPO_SCHEMA: Final[dict[str, object]] = {
    "id": int,
    "description": str,
    "status": TASK_STATUS,
    "created_at": ISO_DATETIME,
    "updated_at": ISO_DATETIME,
}


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
