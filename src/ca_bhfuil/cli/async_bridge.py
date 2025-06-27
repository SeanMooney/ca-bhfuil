"""Bridge for running async code from a synchronous Typer CLI."""

import asyncio
import typing

def run_async(main_coro: typing.Coroutine) -> typing.Any:
    """Run the main async entry point."""
    try:
        return asyncio.run(main_coro)
    except KeyboardInterrupt:
        print("Operation cancelled by user.")
        return None
