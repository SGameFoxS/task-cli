import sys
from tabulate import tabulate
from app.repo import REPO_FILE_PATH, load_tasks, create_task, update_task, delete_task
from datetime import datetime
from app.schemas import Task, TaskRow, TaskStatusEnum
from enum import Enum, unique
from pathlib import Path
from typing import TextIO


@unique
class MessageKind(Enum):
    INFO = "info"
    ERROR = "error"

    @property
    def label(self) -> str:
        return self.value.upper()


def _format_dt(isodt: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    dt = datetime.fromisoformat(isodt).astimezone()
    return dt.strftime(fmt)


def _task_to_row(task: Task) -> TaskRow:
    return {
        "id": task["id"],
        "description": task["description"],
        "status": TaskStatusEnum(task["status"]).label,
        "created_at": _format_dt(task["created_at"]),
        "updated_at": _format_dt(task["updated_at"]),
    }


def _load_tasks_safe(*, repo_path: Path) -> tuple[list[Task] | None, str | None]:
    try:
        return load_tasks(repo_path=repo_path), None
    except (ValueError, OSError, TypeError) as e:
        return None, str(e)


def _print_msg(
    msg: str, kind: MessageKind = MessageKind.INFO, *, file: TextIO = sys.stdout
) -> None:
    print(f"\n{kind.label} : {msg}\n", file=file)


def _print_err(msg: str) -> None:
    _print_msg(msg, MessageKind.ERROR, file=sys.stderr)


def _get_tasks(*, repo_path: Path) -> list[Task] | None:
    tasks, err = _load_tasks_safe(repo_path=repo_path)
    if err is not None:
        _print_err(err)
        return

    return tasks


def _print_tasks(tasks: list[Task]) -> None:
    rows = (_task_to_row(t) for t in tasks)
    print(tabulate(rows, "keys", tablefmt="simple_grid", disable_numparse=True))


def _filter_tasks_by_status(tasks: list[Task], status: TaskStatusEnum) -> list[Task]:
    return [t for t in tasks if t["status"] == status.value]


def _get_tasks_by_status(
    status: TaskStatusEnum, *, repo_path: Path
) -> list[Task] | None:
    tasks = _get_tasks(repo_path=repo_path)
    if tasks is None:
        return

    return _filter_tasks_by_status(tasks, status)


def show_all(*, repo_path: Path = REPO_FILE_PATH) -> None:
    tasks = _get_tasks(repo_path=repo_path)
    if tasks is None:
        return
    if not tasks:
        _print_msg("No tasks have been created yet")
        return

    _print_tasks(tasks)


def show_todo(*, repo_path: Path = REPO_FILE_PATH) -> None:
    tasks = _get_tasks_by_status(TaskStatusEnum.TODO, repo_path=repo_path)
    if tasks is None:
        return
    if not tasks:
        _print_msg("No TODO tasks found")
        return

    _print_tasks(tasks)


def show_in_progress(*, repo_path: Path = REPO_FILE_PATH) -> None:
    tasks = _get_tasks_by_status(TaskStatusEnum.IN_PROGRESS, repo_path=repo_path)
    if tasks is None:
        return
    if not tasks:
        _print_msg("No IN PROGRESS tasks found")
        return

    _print_tasks(tasks)


def show_done(*, repo_path: Path = REPO_FILE_PATH) -> None:
    tasks = _get_tasks_by_status(TaskStatusEnum.DONE, repo_path=repo_path)
    if tasks is None:
        return
    if not tasks:
        _print_msg("No DONE tasks found")
        return

    _print_tasks(tasks)


def add_task(description: str, *, repo_path: Path = REPO_FILE_PATH) -> None:
    try:
        id = create_task(description, repo_path=repo_path)
        _print_msg(f"Task added successfully (ID: {id})")
    except (ValueError, OSError, TypeError) as e:
        _print_err(str(e))


def edit_task(
    task_id: int, description: str, *, repo_path: Path = REPO_FILE_PATH
) -> None:
    try:
        updated = update_task(task_id, description, repo_path=repo_path)
        _print_msg(f"Task {task_id} updated")
        _print_tasks([updated])
    except (ValueError, OSError, TypeError) as e:
        _print_err(str(e))


def remove_task(task_id: int, *, repo_path: Path = REPO_FILE_PATH) -> None:
    try:
        delete_task(task_id, repo_path=repo_path)
        _print_msg(f"Task {task_id} deleted")
    except (ValueError, OSError, TypeError) as e:
        _print_err(str(e))
