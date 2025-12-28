from typing import TypedDict, Literal

TaskStatus = Literal["todo", "in_progress", "done"]

__all__ = ["Task", "TaskStatus"]


class Task(TypedDict):
    id: int
    description: str
    status: TaskStatus
    created_at: str
    updated_at: str
