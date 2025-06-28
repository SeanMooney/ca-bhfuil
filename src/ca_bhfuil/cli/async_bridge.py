"""Bridge for running async code from a synchronous Typer CLI."""

import asyncio
import functools
import typing

from rich import console


rich_console = console.Console()


def run_async(
    main_coro: typing.Coroutine[typing.Any, typing.Any, typing.Any],
) -> typing.Any:
    """Run the main async entry point."""
    try:
        return asyncio.run(main_coro)
    except KeyboardInterrupt:
        rich_console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        return None
    except Exception as e:
        rich_console.print(f"[red]Unexpected error: {e}[/red]")
        raise


def async_command(
    func: typing.Callable[..., typing.Awaitable[typing.Any]],
) -> typing.Callable[..., typing.Any]:
    """Decorator to convert async CLI command to sync."""

    @functools.wraps(func)
    def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        coro = func(*args, **kwargs)
        # Ensure we have a proper coroutine
        if not asyncio.iscoroutine(coro):
            raise TypeError(f"Function {func.__name__} must return a coroutine")
        return run_async(coro)

    return wrapper


async def with_progress(
    operation: typing.Coroutine[typing.Any, typing.Any, typing.Any],
    description: str = "Processing...",
    show_progress: bool = True,
) -> typing.Any:
    """Run an async operation with optional progress display."""
    if not show_progress:
        return await operation

    from rich import progress

    with progress.Progress(
        progress.SpinnerColumn(),
        progress.TextColumn("[progress.description]{task.description}"),
        progress.BarColumn(),
        progress.TaskProgressColumn(),
        console=rich_console,
    ) as progress_bar:
        task = progress_bar.add_task(description, total=None)
        try:
            result = await operation
            progress_bar.update(task, completed=True)
            return result
        except Exception:
            progress_bar.update(task, description=f"[red]Failed: {description}[/red]")
            raise
