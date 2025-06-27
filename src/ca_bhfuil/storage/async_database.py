"""Asynchronous database management using aiosqlite."""

import asyncio
import typing

import aiosqlite

class AsyncDatabaseManager:
    """Manages asynchronous database connections and queries."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._pool: asyncio.Semaphore | None = None

    async def connect(self, pool_size: int = 10):
        """Create a connection pool."""
        self._pool = asyncio.Semaphore(pool_size)

    async def execute(self, sql: str, parameters: list[typing.Any] | None = None) -> aiosqlite.Cursor | None:
        """Execute a single SQL statement."""
        if not self._pool:
            raise ConnectionError("Database not connected. Call connect() first.")

        async with self._pool:
            async with aiosqlite.connect(self._db_path) as db:
                try:
                    cursor = await db.execute(sql, parameters)
                    await db.commit()
                    return cursor
                except Exception as e:
                    await db.rollback()
                    raise e

    async def close(self):
        """Close the connection pool."""
        self._pool = None
