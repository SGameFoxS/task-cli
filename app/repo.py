import json
from pathlib import Path
from schemas import Task, TypedDictType
from typing import Final, Any, Literal, get_origin, get_args, cast

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


def _assert_typed_dict(obj: object, schema: type[TypedDictType]) -> None:
    """
    Assert that `obj` conforms to a TypedDict-like schema at runtime.

    The schema is a TypedDict class (e.g. `Task`). Validation uses:
        - schema.__annotations__   for field names and expected types
        - schema.__required_keys__ for required fields

    Raises:
        ValueError: If `obj` does not match the schema.
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


def _assert_tasks_valid(data: object, *, repo_path: Path = REPO_FILE_PATH) -> None:
    """
    Validate a decoded repository payload.

    The repository payload must be a JSON array (Python list) of Task objects.

    This function does not return the validated tasks. It either:
        - succeeds silently, or
        - raises an exception with details (including an item index and file path).

    Args:
        data: Decoded JSON value (typically returned by `json.load`).
        repo_path: Path included in error messages (useful for editor click-through).

    Raises:
        ValueError: If `data` is not a list or any item is not a valid Task.
    """
    if not isinstance(data, list):
        raise ValueError(REPO_FORMAT_INVALID_ERROR)

    for i, item in enumerate(data):
        try:
            _assert_typed_dict(item, Task)
        except ValueError as e:
            raise ValueError(
                TASK_INVALID_AT_INDEX_ERROR.format(
                    repo_path=repo_path,
                    index=i,
                    detail=e,
                )
            ) from e


def _as_tasks(data: object, *, repo_path: Path = REPO_FILE_PATH) -> list[Task]:
    """
    Validate and cast a decoded JSON value to `list[Task]`.

    This is a small convenience wrapper around `_assert_tasks_valid`.
    If validation succeeds, the returned value is the original list, typed as
    `list[Task]` for static type checkers.

    Args:
        data: Decoded JSON value (typically returned by `json.load`).
        repo_path: Repository file path used in error messages.

    Returns:
        The validated tasks list, typed as `list[Task]`.

    Raises:
        ValueError: If the repository payload is invalid.
    """
    _assert_tasks_valid(data, repo_path=repo_path)
    return cast(list[Task], data)


def load_tasks(*, repo_path: Path = REPO_FILE_PATH) -> list[Task]:
    """
    Load tasks from the JSON repository file.

    Expected file contents:
        A JSON array (list) of task objects.

    Behavior:
        - If the file does not exist: return an empty list.
        - If the file contains invalid JSON: raise ValueError (corrupted file).
        - If the JSON is valid but has an invalid shape: raise ValueError.

    Args:
        repo_path: Path to the repository JSON file.

    Returns:
        A list of validated tasks.

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

    return _as_tasks(data)


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
    _assert_typed_dict(task, Task)

    repo_path.parent.mkdir(parents=True, exist_ok=True)
    data = load_tasks(repo_path=repo_path)

    data.append(task)
    with repo_path.open("w", encoding="utf-8") as repo_file:
        json.dump(data, repo_file, ensure_ascii=False, indent=1)
