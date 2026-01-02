import click
from pathlib import Path
from app.cli import (
    repo_path_cmd,
    show_all_cmd,
    show_todo_cmd,
    show_in_progress_cmd,
    show_done_cmd,
    add_task_cmd,
    update_task_cmd,
    delete_task_cmd,
    mark_in_progress_cmd,
    mark_done_cmd,
)

__all__ = ("repo", "list", "add", "update", "delete", "mark_in_progress", "mark_done")


@click.command
@click.pass_obj
def repo(repo_path: Path) -> None:
    """
    Print the currently selected repository file path.
    """
    repo_path_cmd(repo_path=repo_path)


@click.group
def list() -> None:
    """
    List tasks in the repository.
    """
    pass


@list.command("all")
@click.pass_obj
def list_all(repo_path: Path) -> None:
    """
    List all tasks.
    """
    show_all_cmd(repo_path=repo_path)


@list.command("todo")
@click.pass_obj
def list_todo(repo_path: Path) -> None:
    """
    List TODO tasks.
    """
    show_todo_cmd(repo_path=repo_path)


@list.command("in-progress")
@click.pass_obj
def list_in_progress(repo_path: Path) -> None:
    """
    List IN PROGRESS tasks.
    """
    show_in_progress_cmd(repo_path=repo_path)


@list.command("done")
@click.pass_obj
def list_done(repo_path: Path) -> None:
    """
    List DONE tasks.
    """
    show_done_cmd(repo_path=repo_path)


@click.command
@click.argument("description")
@click.pass_obj
def add(repo_path: Path, description: str) -> None:
    """
    Add a new task to the repository.
    """
    add_task_cmd(description, repo_path=repo_path)


@click.command
@click.argument("task_id", type=int)
@click.argument("description")
@click.pass_obj
def update(repo_path: Path, task_id: int, description: str) -> None:
    """
    Edit an existing task description.
    """
    update_task_cmd(task_id, description, repo_path=repo_path)


@click.command
@click.argument("task_id", type=int)
@click.pass_obj
def delete(repo_path: Path, task_id: int) -> None:
    """
    Remove a task from the repository.
    """
    delete_task_cmd(task_id, repo_path=repo_path)


@click.command("mark-in-progress")
@click.argument("task_id", type=int)
@click.pass_obj
def mark_in_progress(repo_path: Path, task_id: int) -> None:
    """
    Mark a task as IN PROGRESS.
    """
    mark_in_progress_cmd(task_id, repo_path=repo_path)


@click.command("mark-done")
@click.argument("task_id", type=int)
@click.pass_obj
def mark_done(repo_path: Path, task_id: int) -> None:
    """
    Mark a task as DONE.
    """
    mark_done_cmd(task_id, repo_path=repo_path)
