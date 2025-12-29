import json
from pathlib import Path
from schemas import Task, TypedDictType
from typing import Final, Any, Literal, get_origin, get_args

REPO_DIR_NAME: Final[str] = "data"
REPO_DIR_PATH: Final[Path] = Path(__file__).resolve().parents[1] / REPO_DIR_NAME

REPO_FILE_NAME: Final[str] = "tasks.json"
REPO_FILE_PATH: Final[Path] = REPO_DIR_PATH / REPO_FILE_NAME

REPO_CORRUPTED_ERROR: Final[str] = "Corrupted repository file ({repo_path})"
REPO_FORMAT_INVALID_ERROR: Final[str] = (
    "Repository format is invalid: expected a list of tasks"
)

VALIDATION_EXPECTED_DICT_ERROR: Final[str] = "Expected dict object, got {got}"
VALIDATION_MISSING_KEYS_ERROR: Final[str] = "Missing keys: {keys}"
VALIDATION_UNEXPECTED_KEYS_ERROR: Final[str] = "Unexpected keys: {keys}"
VALIDATION_INVALID_TYPE_ERROR: Final[str] = (
    "Invalid type for {key!r}: expected {expected}, got {got!r}"
)

TASK_INVALID_AT_INDEX_ERROR: Final[str] = (
    "Invalid task at index {index}. {detail} ({repo_path})"
)


def _check_value_type(value: Any, expected_type: Any) -> bool:
    """
    Return True if `value` matches `expected_type`.

    Supported checks:
      - Literal[...]    (e.g. Literal["todo", "done"])
      - builtin/classes (e.g. int, str)

    Note:
      This is a minimal runtime type checker for repository validation.
      It does not support containers (list[T], dict[K, V]), Union/Optional, etc.
    """

    origin = get_origin(expected_type)

    if origin is Literal:
        return value in get_args(expected_type)

    if isinstance(expected_type, type):
        return isinstance(value, expected_type)

    return False


def _type_repr(expected_type: Any) -> str:
    """
    Human-readable representation of an expected type for error messages.

    Examples:
      - Literal["a", "b"] -> "'a' or 'b'"
      - str -> "str"
    """

    origin = get_origin(expected_type)

    if origin is Literal:
        allowed = " or ".join(repr(arg) for arg in get_args(expected_type))
        return allowed

    if isinstance(expected_type, type):
        return expected_type.__name__

    return str(expected_type)


def _validate_typed_dict(obj: Any, schema: type[TypedDictType]) -> dict[str, Any]:
    """
    Validate that `obj` conforms to a TypedDict-like schema.

    The schema is provided as a TypedDict class (e.g. `Task`) and is inspected via:
      - schema.__annotations__     (field names and expected types)
      - schema.__required_keys__   (required fields)
      - schema.__optional_keys__   (optional fields)

    Validation performed:
      - `obj` must be a dict
      - all required keys must be present
      - no unexpected keys are allowed
      - values of present keys must match expected types (see `_check_value_type`)

    Returns:
      The same dict object (useful for chaining), typed as dict[str, Any].

    Raises:
      ValueError: if the object does not match the schema.
    """

    if not isinstance(obj, dict):
        raise ValueError(VALIDATION_EXPECTED_DICT_ERROR.format(got=type(obj).__name__))

    ann = schema.__annotations__

    # required keys
    missing = [k for k in ann if k not in obj and k in schema.__required_keys__]
    if missing:
        raise ValueError(VALIDATION_MISSING_KEYS_ERROR.format(keys=missing))

    # extra keys
    extra = [k for k in obj if k not in ann and k not in schema.__optional_keys__]
    if extra:
        raise ValueError(VALIDATION_UNEXPECTED_KEYS_ERROR.format(keys=extra))

    # type check
    for key, expected_type in ann.items():
        if key not in obj:
            continue

        value = obj[key]
        if not _check_value_type(value, expected_type):
            raise ValueError(
                VALIDATION_INVALID_TYPE_ERROR.format(
                    key=key,
                    expected=_type_repr(expected_type),
                    got=value,
                )
            )

    return obj


def _validate_tasks(data: Any, *, repo_path: Path = REPO_FILE_PATH) -> list[Task]:
    """
    Validate repository payload decoded from JSON.

    The repository format must be a list of Task objects.

    Args:
        data: Decoded JSON value (typically from `json.load`).
        repo_path: Repository file path, included in error messages to make
            them clickable in some editors (e.g. VS Code).

    Returns:
        A list of validated tasks.

    Raises:
        ValueError: if `data` is not a list, or any item is not a valid Task.
    """

    if not isinstance(data, list):
        raise ValueError(REPO_FORMAT_INVALID_ERROR)

    res: list[Task] = []

    for i, item in enumerate(data):
        try:
            _validate_typed_dict(item, Task)
        except ValueError as e:
            raise ValueError(
                TASK_INVALID_AT_INDEX_ERROR.format(
                    repo_path=repo_path,
                    index=i,
                    detail=e,
                )
            ) from e

        res.append(item)

    return res


def load_tasks(*, repo_path: Path = REPO_FILE_PATH) -> list[Task]:
    """
    Load tasks from the JSON repository file.

    Expected file contents:
      - a JSON array (list) of task objects

    Behavior:
      - if the file does not exist: returns an empty list
      - if the JSON is invalid: raises ValueError(REPO_CORRUPTED_ERROR)
      - if the JSON is valid but has the wrong shape: raises ValueError

    Args:
        repo_path: Path to the repository JSON file.

    Returns:
        A list of validated tasks.

    Raises:
        ValueError: If the repository file contains invalid JSON (corrupted),
            or if the decoded JSON has an invalid format.
        OSError: If the file cannot be read due to filesystem-related errors.
    """

    try:
        with repo_path.open(encoding="utf-8") as repo_file:
            data = json.load(repo_file)
    except FileNotFoundError:
        data = []
    except json.JSONDecodeError as e:
        raise ValueError(REPO_CORRUPTED_ERROR.format(repo_path=repo_path)) from e

    return _validate_tasks(data)


def save_task(task: Task, *, repo_path: Path = REPO_FILE_PATH) -> None:
    """
    Append a task to the JSON repository file.

    Notes:
      - `task` is validated against the Task schema before writing.
      - Existing repository contents are loaded and validated as well.
      - Parent directories are created automatically.

    Args:
        task: Task object to append to the repository (must be JSON-serializable).
        repo_path: Path to the repository JSON file.

    Raises:
        ValueError: If `task` is invalid, or the repository file is corrupted,
            or the repository contents have an invalid format.
        OSError: If the file or directories cannot be created/read/written.
        TypeError: If the resulting data cannot be JSON-serialized.
    """

    _validate_typed_dict(task, Task)

    repo_path.parent.mkdir(parents=True, exist_ok=True)
    data = load_tasks(repo_path=repo_path)

    data.append(task)
    with repo_path.open("w", encoding="utf-8") as repo_file:
        json.dump(data, repo_file, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    new_task: Task = {
        "id": 1,
        "description": "Example Task",
        "status": "todo",
        "created_at": "2024-06-01T12:00:00Z",
        "updated_at": "2024-06-01T12:00:00Z",
    }

    save_task(new_task)
