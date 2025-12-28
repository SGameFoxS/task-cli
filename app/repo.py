import json
from pathlib import Path
from schemas import Task
from typing import Final

REPO_DIR_NAME: Final[str] = "data"
REPO_DIR_PATH: Final[Path] = Path(__file__).resolve().parents[1] / REPO_DIR_NAME

REPO_FILE_NAME: Final[str] = "tasks.json"
REPO_FILE_PATH: Final[Path] = REPO_DIR_PATH / REPO_FILE_NAME

REPO_CORRUPTED_ERROR: Final[str] = "Corrupted repository file ({repo_path})"
REPO_FORMAT_INVALID_ERROR: Final[str] = (
    "Repository format is invalid: expected a list of tasks"
)


def save_task(task: Task, *, repo_path: Path = REPO_FILE_PATH) -> None:
    """
    Append a task to the JSON repository file.

    The repository file is expected to contain a JSON array (a list)
    of tasks. If the file does not exist, it will be created along with
    its parent directories.

    Args:
        task: Task object to append to the repository (must be JSON-serializable).

        repo_path: Path to the repository JSON file.

    Raises:
        ValueError: If the repository file contains invalid JSON (corrupted),
            or if the decoded JSON is not a list (invalid repository format).

        OSError: If the file or directories cannot be created/read/written due
            to filesystem-related errors (permissions, IO issues, ...).

        TypeError: If `task` (or repository contents) are not JSON-serializable
            when writing.
    """

    repo_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with repo_path.open(encoding="utf-8") as repo_file:
            data = json.load(repo_file)
    except FileNotFoundError:
        data = []
    except json.JSONDecodeError as e:
        raise ValueError(REPO_CORRUPTED_ERROR.format(repo_path=repo_path)) from e

    if not isinstance(data, list):
        raise ValueError(REPO_FORMAT_INVALID_ERROR)

    data.append(task)

    with repo_path.open("w", encoding="utf-8") as repo_file:
        json.dump(data, repo_file, ensure_ascii=False, indent=1)
