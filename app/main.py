import click
from pathlib import Path

from app.commands import repo, list, add, update, delete, mark_in_progress, mark_done
from app.repo import REPO_FILE_PATH


@click.group
@click.option(
    "--repo-path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=REPO_FILE_PATH,
    show_default=True,
    help="Path to the tasks JSON repository file.",
)
@click.pass_context
def cli(ctx: click.Context, repo_path: Path) -> None:
    """
    Simple task manager CLI backed by a JSON file repository.
    """
    ctx.obj = repo_path


cli.add_command(repo)
cli.add_command(list)
cli.add_command(add)
cli.add_command(update)
cli.add_command(delete)
cli.add_command(mark_in_progress)
cli.add_command(mark_done)


if __name__ == "__main__":
    cli()
