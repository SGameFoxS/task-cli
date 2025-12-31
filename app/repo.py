import json
from pathlib import Path
from schemas import Task, TypedDictType, TaskStatusEnum
from typing import Final, Any, Literal, get_origin, get_args, cast, TypeVar
from datetime import datetime, timezone

__all__ = ("load_tasks", "save_task", "create_task")

REPO_DIR_NAME: Final[str] = "data"
REPO_DIR_PATH: Final[Path] = Path(__file__).resolve().parents[1] / REPO_DIR_NAME

REPO_FILE_NAME: Final[str] = "tasks.json"
REPO_FILE_PATH: Final[Path] = REPO_DIR_PATH / REPO_FILE_NAME

REPO_CORRUPTED_ERROR: Final[str] = "Corrupted repository file ({repo_path})"
REPO_FORMAT_INVALID_ERROR: Final[str] = (
    "Repository format is invalid: expected a JSON array (list) of items"
)

VALIDATION_EXPECTED_DICT_ERROR: Final[str] = "Expected JSON object (dict), got {got}"
VALIDATION_MISSING_KEYS_ERROR: Final[str] = "Missing keys: {keys}"
VALIDATION_UNEXPECTED_KEYS_ERROR: Final[str] = "Unexpected keys: {keys}"
VALIDATION_INVALID_TYPE_ERROR: Final[str] = (
    "Invalid type for {key!r}: expected {expected}, got {got!r}"
)

ITEM_INVALID_AT_INDEX_ERROR: Final[str] = (
    "Invalid item at index {index}. {detail} ({repo_path})"
)

TASK_NOT_FOUND_ERROR: Final[str] = "Task with id {task_id!r} not found"

T = TypeVar("T", bound=TypedDictType)


def _check_value_type(value: Any, expected_type: Any) -> bool:
    """
    Return True if `value` matches `expected_type`.

    Supported checks:
        - Literal[...] (e.g. Literal["todo", "done"])
        - plain classes / builtins (e.g. int, str)

    Notes:
        This is a minimal runtime checker used for repository validation.
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
    Return a human-readable representation of `expected_type` for error messages.

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


def _assert_typed_dict(obj: object, schema: type[T]) -> None:
    """
    Assert that `obj` conforms to the given TypedDict schema at runtime.

    The schema is a TypedDict class (e.g. `Task`). Validation uses:
        - schema.__annotations__   for field names and expected types
        - schema.__required_keys__ for required fields

    Raises:
        ValueError: If `obj` is not a dict or does not match the schema.
    """
    if not isinstance(obj, dict):
        raise ValueError(VALIDATION_EXPECTED_DICT_ERROR.format(got=type(obj).__name__))

    ann = schema.__annotations__

    # required keys
    missing = [k for k in ann if k not in obj and k in schema.__required_keys__]
    if missing:
        raise ValueError(VALIDATION_MISSING_KEYS_ERROR.format(keys=missing))

    # extra keys
    extra = [k for k in obj if k not in ann]
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


def _assert_list_valid(data: object, *, schema: type[T], repo_path: Path) -> None:
    """
    Validate a decoded repository payload.

    Expected payload:
        A JSON array (Python list) where each element is an object (dict)
        matching `schema`.

    This function does not return the validated list. It either:
        - succeeds silently, or
        - raises an exception with details (including an item index and file path).

    Args:
        data: Decoded JSON value (typically returned by `json.load`).
        schema: TypedDict schema used to validate each list element.
        repo_path: Path included in error messages (useful for editor click-through).

    Raises:
        ValueError: If `data` is not a list or any element does not match `schema`.
    """
    if not isinstance(data, list):
        raise ValueError(REPO_FORMAT_INVALID_ERROR)

    for i, item in enumerate(data):
        try:
            _assert_typed_dict(item, schema)
        except ValueError as e:
            raise ValueError(
                ITEM_INVALID_AT_INDEX_ERROR.format(
                    repo_path=repo_path,
                    index=i,
                    detail=e,
                )
            ) from e


def _as_list(data: object, *, schema: type[T], repo_path: Path) -> list[T]:
    """
    Validate and cast a decoded JSON value to `list[T]`.

    This is a convenience wrapper around `_assert_list_valid`.
    If validation succeeds, the returned value is the original list, typed as
    `list[T]` for static type checkers.

    Args:
        data: Decoded JSON value (typically returned by `json.load`).
        schema: TypedDict schema used to validate each list element.
        repo_path: Repository file path used in error messages.

    Returns:
        The validated list (same object), typed as `list[T]`.

    Raises:
        ValueError: If the repository payload is invalid.
    """
    _assert_list_valid(data, schema=schema, repo_path=repo_path)
    return cast(list[T], data)


def _load(*, schema: type[T], repo_path: Path) -> list[T]:
    """
    Load and validate a list of items from a JSON repository file.

    Expected file contents:
        A JSON array (list) of objects matching `schema`.

    Behavior:
        - If the file does not exist: returns an empty list.
        - If the file contains invalid JSON: raises ValueError (corrupted file).
        - If the JSON is valid but has an invalid shape: raises ValueError.

    Args:
        schema: TypedDict schema used to validate each list element.
        repo_path: Path to the repository JSON file.

    Returns:
        A list of validated items, typed as `list[T]`.

    Raises:
        ValueError: If the JSON is corrupted or the decoded payload is invalid.
        OSError: If the file cannot be read due to filesystem-related errors.
    """
    try:
        with repo_path.open(encoding="utf-8") as repo_file:
            data: object = json.load(repo_file)
    except FileNotFoundError:
        data = []
    except json.JSONDecodeError as e:
        raise ValueError(REPO_CORRUPTED_ERROR.format(repo_path=repo_path)) from e

    return _as_list(data, schema=schema, repo_path=repo_path)


def _write_all(items: list[T], *, repo_path: Path, indent: int | None = 1) -> None:
    """
    Write the full repository payload to disk.

    Notes:
        - Parent directories are created automatically.
        - The repository file is overwritten.

    Args:
        items: List of JSON-serializable items to write.
        repo_path: Path to the repository JSON file.
        indent: JSON indentation level. Use `None` for compact output.

    Raises:
        OSError: If the file cannot be created/opened/written.
        TypeError: If `items` cannot be JSON-serialized.
    """
    repo_path.parent.mkdir(parents=True, exist_ok=True)

    with repo_path.open("w", encoding="utf-8") as repo_file:
        json.dump(items, repo_file, ensure_ascii=False, indent=indent)


def _save(item: T, *, schema: type[T], repo_path: Path) -> None:
    """
    Append an item to the JSON repository file.

    Notes:
        - `item` is validated against `schema` before writing.
        - Existing repository contents are loaded and validated as well.

    Args:
        item: Item to append (must be JSON-serializable).
        schema: TypedDict schema used to validate `item` and repository contents.
        repo_path: Path to the repository JSON file.

    Raises:
        ValueError: If `item` is invalid, the repository file is corrupted,
            or the repository contents have an invalid format.
        OSError: If the file or directories cannot be created/read/written.
        TypeError: If the resulting payload cannot be JSON-serialized.
    """
    _assert_typed_dict(item, schema=schema)

    data = _load(schema=schema, repo_path=repo_path)

    data.append(item)

    _write_all(data, repo_path=repo_path)


def load_tasks(*, repo_path: Path = REPO_FILE_PATH) -> list[Task]:
    """
    Load tasks from the JSON repository file.

    Expected file contents:
        A JSON array (list) of task objects.

    Behavior:
        - If the file does not exist: returns an empty list.
        - If the file contains invalid JSON: raises ValueError (corrupted file).
        - If the JSON is valid but has an invalid shape: raises ValueError.

    Args:
        repo_path: Path to the repository JSON file.

    Returns:
        A list of validated tasks.

    Raises:
        ValueError: If the JSON is corrupted or the decoded payload is invalid.
        OSError: If the file cannot be read due to filesystem-related errors.
    """
    return _load(schema=Task, repo_path=repo_path)


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
        ValueError: If `task` is invalid, the repository file is corrupted,
            or the repository contents have an invalid format.
        OSError: If the file or directories cannot be created/read/written.
        TypeError: If the resulting payload cannot be JSON-serialized.
    """
    _save(task, schema=Task, repo_path=repo_path)


def create_task(
    description: str,
    status: TaskStatusEnum = TaskStatusEnum.TODO,
    *,
    repo_path: Path = REPO_FILE_PATH,
) -> None:
    """
    Create a new task and persist it in the JSON repository.

    A task is assigned a monotonically increasing integer `id` based on the
    current maximum id in the repository (`max_id + 1`). Timestamps are set
    in UTC using ISO 8601 format.

    Notes:
        - Although `status` is provided as `TaskStatusEnum`, the repository stores
          the status as a plain string (`status.value`) to keep the JSON
          representation simple and compatible with the Task schema.
        - This function writes the task immediately via `save_task` and does not
          return the created task.

    Args:
        description: Human-readable task description.
        status: Initial task status as an enum value. Defaults to `TODO`.
        repo_path: Path to the repository JSON file.

    Raises:
        ValueError: If the repository file is corrupted or contains invalid data,
            or if the produced task does not match the Task schema.
        OSError: If the repository file cannot be read or written due to
            filesystem-related errors.
        TypeError: If the resulting payload cannot be JSON-serialized.
    """
    data = load_tasks(repo_path=repo_path)

    next_id = max((task["id"] for task in data), default=0) + 1
    now = datetime.now(timezone.utc).isoformat()

    task: Task = {
        "id": next_id,
        "description": description,
        "status": status.value,
        "created_at": now,
        "updated_at": now,
    }

    save_task(task)


def delete_task(task_id: int, *, repo_path: Path = REPO_FILE_PATH) -> None:
    """
    Delete a task from the repository by its integer id.

    Args:
        task_id: Task id to delete.
        repo_path: Path to the repository JSON file.

    Raises:
        ValueError: If no task with the given id exists, or if the repository
            file is corrupted/invalid.
        OSError: If the file cannot be read or written due to filesystem errors.
        TypeError: If the resulting payload cannot be JSON-serialized.
    """
    data = load_tasks(repo_path=repo_path)

    idx = next((i for i, t in enumerate(data) if t["id"] == task_id), None)
    if idx is None:
        raise ValueError(TASK_NOT_FOUND_ERROR.format(task_id=task_id))

    del data[idx]

    _write_all(data, repo_path=repo_path)
