"""Asynchronous error handling and resilience patterns."""

import asyncio
import random
import typing

class AsyncErrorHandler:
    """Provides async error handling utilities like retry."""

    def __init__(self, attempts: int = 3, initial_backoff: float = 0.5, max_backoff: float = 5.0, jitter: bool = True):
        self.attempts = attempts
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.jitter = jitter

    async def retry(self, coro: Coroutine, retry_on: Type[Exception] | Tuple[Type[Exception], ...]) -> Any:
        """Retry a coroutine with exponential backoff."""
        backoff = self.initial_backoff
        for attempt in range(self.attempts):
            try:
                return await coro
            except retry_on as e:
                if attempt == self.attempts - 1:
                    raise e
                
                sleep_time = backoff
                if self.jitter:
                    sleep_time += random.uniform(0, backoff * 0.1)
                
                await asyncio.sleep(sleep_time)
                backoff = min(self.max_backoff, backoff * 2)
