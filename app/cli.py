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


def show_info(msg: str, kind: MessageKind = MessageKind.INFO) -> None:
    print(tabulate([[kind.label, msg]], tablefmt="simple_grid", disable_numparse=True))


def show_all_tasks(*, repo_path: Path = REPO_FILE_PATH) -> None:
    tasks = load_tasks(repo_path=repo_path)

    if not tasks:
        show_info("No tasks have been created yet")
        return

    rows = (_task_to_row(t) for t in tasks)
    print(tabulate(rows, "keys", tablefmt="simple_grid"))


if __name__ == "__main__":
    show_all_tasks()
