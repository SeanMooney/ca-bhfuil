"""Asynchronous task management."""

import asyncio
import typing
import uuid

from ca_bhfuil.core.models import progress


class AsyncTaskManager:
    """Manages background tasks."""

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task[typing.Any]] = {}
        self._results: dict[str, typing.Any] = {}
        self._status: dict[str, progress.TaskStatus] = {}

    def create_task(
        self, coro: typing.Coroutine[typing.Any, typing.Any, typing.Any]
    ) -> str:
        """Create and track a new background task."""
        task_id = str(uuid.uuid4())
        task = asyncio.create_task(self._run_task(task_id, coro))
        self._tasks[task_id] = task
        self._status[task_id] = progress.TaskStatus.RUNNING
        return task_id

    async def _run_task(
        self, task_id: str, coro: typing.Coroutine[typing.Any, typing.Any, typing.Any]
    ) -> None:
        """Run a task and store its result."""
        try:
            result = await coro
            self._results[task_id] = result
            self._status[task_id] = progress.TaskStatus.COMPLETED
        except Exception as e:
            self._results[task_id] = e
            self._status[task_id] = progress.TaskStatus.FAILED

    def get_status(self, task_id: str) -> progress.TaskStatus:
        """Get the status of a task."""
        return self._status.get(task_id, progress.TaskStatus.PENDING)

    def get_result(self, task_id: str) -> typing.Any:
        """Get the result of a completed task."""
        return self._results.get(task_id)
