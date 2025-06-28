"""Asynchronous operation monitoring."""

from functools import wraps
import time
import typing


class AsyncOperationMonitor:
    """Monitors asynchronous operations, tracking timing and success."""

    def __init__(self) -> None:
        self.stats: dict[str, dict[str, typing.Any]] = {}

    def timed(
        self,
        func: typing.Callable[
            ..., typing.Coroutine[typing.Any, typing.Any, typing.Any]
        ],
    ) -> typing.Callable[..., typing.Coroutine[typing.Any, typing.Any, typing.Any]]:
        """A decorator to time an asynchronous function."""

        @wraps(func)
        async def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            start_time = time.monotonic()
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception:
                success = False
                raise
            finally:
                end_time = time.monotonic()
                duration = end_time - start_time
                self._update_stats(func.__name__, duration, success)

        return wrapper

    def _update_stats(self, name: str, duration: float, success: bool) -> None:
        """Update the statistics for a given operation."""
        if name not in self.stats:
            self.stats[name] = {
                "calls": 0,
                "success": 0,
                "failure": 0,
                "total_duration": 0.0,
            }

        self.stats[name]["calls"] += 1
        if success:
            self.stats[name]["success"] += 1
        else:
            self.stats[name]["failure"] += 1
        self.stats[name]["total_duration"] += duration
