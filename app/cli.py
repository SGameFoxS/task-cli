from tabulate import tabulate
from app.repo import load_tasks, REPO_FILE_PATH
from datetime import datetime
from app.schemas import Task, TaskRow, TaskStatusEnum
from enum import Enum, unique
from pathlib import Path


@unique
class MessageKind(Enum):
    INFO = "info"
    ERROR = "error"

    @property
    def label(self) -> str:
        return self.value.upper()


def _format_dt(isodt: str) -> str:
    dt = datetime.fromisoformat(isodt)
    dt = dt.astimezone()

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _task_to_row(task: Task) -> TaskRow:
    return {
        "id": task["id"],
        "description": task["description"],
        "status": TaskStatusEnum(task["status"]).label,
        "created_at": _format_dt(task["created_at"]),
        "updated_at": _format_dt(task["updated_at"]),
    }


def _show_info(msg: str, kind: MessageKind = MessageKind.INFO) -> None:
    print(tabulate([[kind.label, msg]], tablefmt="simple_grid", disable_numparse=True))


def _show_tasks(tasks: list[Task]) -> None:
    rows = (_task_to_row(t) for t in tasks)
    print(tabulate(rows, "keys", tablefmt="simple_grid"))


def _filter_tasks_by_status(tasks: list[Task], status: TaskStatusEnum) -> list[Task]:
    return [t for t in tasks if t["status"] == status.value]


def _get_tasks_by_status(status: TaskStatusEnum, *, repo_path) -> list[Task]:
    return _filter_tasks_by_status(load_tasks(repo_path=repo_path), status)


def show_all_tasks(*, repo_path: Path = REPO_FILE_PATH) -> None:
    tasks = load_tasks(repo_path=repo_path)
    if not tasks:
        _show_info("No tasks have been created yet")
        return

    _show_tasks(tasks)


def show_todo_tasks(*, repo_path: Path = REPO_FILE_PATH) -> None:
    tasks = _get_tasks_by_status(TaskStatusEnum.TODO, repo_path=repo_path)
    if not tasks:
        _show_info("No TODO tasks found")
        return

    _show_tasks(tasks)


def show_in_progress_tasks(*, repo_path: Path = REPO_FILE_PATH) -> None:
    tasks = _get_tasks_by_status(TaskStatusEnum.IN_PROGRESS, repo_path=repo_path)
    if not tasks:
        _show_info("No IN PROGRESS tasks found")
        return

    _show_tasks(tasks)


def show_done_tasks(*, repo_path: Path = REPO_FILE_PATH) -> None:
    tasks = _get_tasks_by_status(TaskStatusEnum.DONE, repo_path=repo_path)
    if not tasks:
        _show_info("No DONE tasks found")
        return

    _show_tasks(tasks)
