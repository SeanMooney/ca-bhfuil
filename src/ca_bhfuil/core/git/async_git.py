"""Asynchronous Git operations using a thread pool executor."""

import asyncio
from concurrent import futures
import typing


class AsyncGitManager:
    """Manages running synchronous pygit2 operations in a thread pool."""

    def __init__(self, max_workers: int = 4):
        self._executor = futures.ThreadPoolExecutor(max_workers=max_workers)

    async def run_in_executor(
        self, func: typing.Callable[..., typing.Any], *args: typing.Any
    ) -> typing.Any:
        """Run a synchronous function in the thread pool."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, func, *args)

    def shutdown(self) -> None:
        """Shutdown the thread pool executor."""
        self._executor.shutdown(wait=True)
