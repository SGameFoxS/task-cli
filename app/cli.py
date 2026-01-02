import sys
import functools
from tabulate import tabulate
from app.repo import (
    REPO_FILE_PATH,
    load_tasks,
    create_task,
    update_task,
    delete_task,
    mark_task_in_progress,
    mark_task_done,
)
from datetime import datetime
from app.schemas import Task, TaskRow, LoadTasksOk, LoadTasksErr
from pathlib import Path
from enums import TaskStatusEnum, MessageKind
from typing import TextIO, Callable, TypeVar, ParamSpec

__all__ = (
    "show_all",
    "show_todo",
    "show_in_progress",
    "show_done",
    "add_task",
    "edit_task",
    "remove_task",
    "mark_in_progress",
    "mark_done",
)

_T = TypeVar("_T")
_P = ParamSpec("_P")

type _LoadTasksResult = LoadTasksOk | LoadTasksErr


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


def _load_tasks_safe(*, repo_path: Path) -> _LoadTasksResult:
    try:
        return LoadTasksOk(success=True, value=load_tasks(repo_path=repo_path))
    except (ValueError, OSError, TypeError) as e:
        return LoadTasksErr(success=False, msg=str(e))


def _print_msg(
    msg: str, kind: MessageKind = MessageKind.INFO, *, file: TextIO = sys.stdout
) -> None:
    print(f"\n{kind.label} : {msg}\n", file=file)


def _print_err(msg: str) -> None:
    _print_msg(msg, MessageKind.ERROR, file=sys.stderr)


def _get_tasks(*, repo_path: Path) -> list[Task] | None:
    res = _load_tasks_safe(repo_path=repo_path)
    if res.success is False:
        _print_err(res.msg)
        return

    return res.value


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


def _safe_action(
    *, handled: tuple[type[Exception], ...] = (ValueError, OSError, TypeError)
) -> Callable[[Callable[_P, _T]], Callable[_P, _T | None]]:
    def deco(fn: Callable[_P, _T]) -> Callable[_P, _T | None]:
        @functools.wraps(fn)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T | None:
            try:
                return fn(*args, **kwargs)
            except handled as e:
                _print_err(str(e))

        return wrapper

    return deco


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


@_safe_action()
def add_task(description: str, *, repo_path: Path = REPO_FILE_PATH) -> None:
    id = create_task(description, repo_path=repo_path)
    _print_msg(f"Task added successfully (ID: {id})")


@_safe_action()
def edit_task(
    task_id: int, description: str, *, repo_path: Path = REPO_FILE_PATH
) -> None:
    updated = update_task(task_id, description, repo_path=repo_path)
    _print_msg(f"Task {task_id} updated")
    _print_tasks([updated])


@_safe_action()
def remove_task(task_id: int, *, repo_path: Path = REPO_FILE_PATH) -> None:
    delete_task(task_id, repo_path=repo_path)
    _print_msg(f"Task {task_id} deleted")


@_safe_action()
def mark_in_progress(task_id: int, *, repo_path: Path = REPO_FILE_PATH) -> None:
    marked = mark_task_in_progress(task_id, repo_path=repo_path)
    _print_msg(f"Task {task_id} marked as IN PROGRESS")
    _print_tasks([marked])


@_safe_action()
def mark_done(task_id: int, *, repo_path: Path = REPO_FILE_PATH) -> None:
    marked = mark_task_done(task_id, repo_path=repo_path)
    _print_msg(f"Task {task_id} marked as DONE")
    _print_tasks([marked])
