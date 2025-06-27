"""Asynchronous progress tracking for concurrent operations."""

import asyncio
import typing

from ca_bhfuil.core.models import progress

class AsyncProgressTracker:
    """Tracks progress of multiple asynchronous operations using a queue."""

    def __init__(self, progress_callback: typing.Callable[[progress.OperationProgress], typing.Awaitable[None]]):
        self._queue = asyncio.Queue()
        self._callback = progress_callback
        self._consumer_task = asyncio.create_task(self._consume_progress())

    async def _consume_progress(self):
        """Consume progress updates from the queue and invoke the callback."""
        while True:
            progress = await self._queue.get()
            if progress is None:  # Sentinel value to stop the consumer
                break
            await self._callback(progress)
            self._queue.task_done()

    def report_progress(self, progress: OperationProgress):
        """Put a progress update into the queue from a synchronous context."""
        asyncio.run_coroutine_threadsafe(self._queue.put(progress), asyncio.get_running_loop())

    async def shutdown(self):
        """Shutdown the progress tracker."""
        await self._queue.put(None)
        await self._queue.join()
        self._consumer_task.cancel()
