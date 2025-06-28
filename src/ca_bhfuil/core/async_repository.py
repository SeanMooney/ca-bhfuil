"""Asynchronous repository management."""

import asyncio
import typing


class AsyncRepositoryManager:
    """Manages concurrent repository operations."""

    def __init__(self, max_concurrent_tasks: int = 5):
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def run_concurrently(
        self, tasks: list[typing.Awaitable[typing.Any]]
    ) -> list[typing.Any]:
        """Run a list of awaitables concurrently, with a semaphore."""

        async def wrapper(
            task: typing.Awaitable[typing.Any],
        ) -> typing.Any:
            async with self._semaphore:
                return await task

        return await asyncio.gather(
            *[wrapper(task) for task in tasks], return_exceptions=True
        )
