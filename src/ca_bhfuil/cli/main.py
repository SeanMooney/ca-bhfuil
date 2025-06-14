"""Main CLI application for ca-bhfuil."""

from pathlib import Path

import typer
from loguru import logger

from ca_bhfuil.core.config import get_settings
from ca_bhfuil.storage import get_cache_manager, get_database_manager

app = typer.Typer(
    name="ca-bhfuil",
    help="Git repository analysis tool for tracking commits across stable branches",
    no_args_is_help=True,
)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query (SHA, partial SHA, or commit message pattern)"),
    repo_path: Path | None = typer.Option(
        None,
        "--repo",
        "-r",
        help="Path to git repository (defaults to current directory)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Search for commits in the repository."""
    if verbose:
        logger.configure(handlers=[{"sink": logger._core.handlers[0]._sink, "level": "DEBUG"}])

    repo_path = repo_path or Path.cwd()

    typer.echo(f"Searching for '{query}' in repository: {repo_path}")
    typer.echo("🚧 Search functionality not yet implemented")


@app.command()
def status(
    repo_path: Path | None = typer.Option(
        None,
        "--repo",
        "-r",
        help="Path to git repository (defaults to current directory)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Show repository analysis status."""
    if verbose:
        logger.configure(handlers=[{"sink": logger._core.handlers[0]._sink, "level": "DEBUG"}])

    repo_path = repo_path or Path.cwd()

    # Get system status
    settings = get_settings()
    cache_manager = get_cache_manager()
    db_manager = get_database_manager()

    typer.echo(f"📁 Repository: {repo_path}")
    typer.echo(f"⚙️  Config directory: {settings.config_dir}")
    typer.echo(f"💾 Cache directory: {settings.cache.directory}")

    # Cache stats
    cache_stats = cache_manager.stats()
    typer.echo(f"📊 Cache entries: {cache_stats.get('count', 0)}")

    # Database stats
    db_stats = db_manager.get_stats()
    typer.echo(f"🗄️  Database repositories: {db_stats['repositories']}")
    typer.echo(f"🗄️  Database commits: {db_stats['commits']}")

    typer.echo("✅ Ca-bhfuil is ready for git analysis!")


def version_callback(value: bool) -> None:
    """Version callback function."""
    if value:
        typer.echo("ca-bhfuil 0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Ca-Bhfuil: Git repository analysis tool for open source maintainers."""
    app()


if __name__ == "__main__":
    app()
