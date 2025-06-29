"""Asynchronous database management using executor pattern with sync database."""

import asyncio
import concurrent.futures
import pathlib
import typing

from loguru import logger

from ca_bhfuil.core import config
from ca_bhfuil.storage.database import schema


class AsyncDatabaseManager:
    """Manages asynchronous database operations using executor pattern."""

    def __init__(self, db_path: pathlib.Path | None = None):
        """Initialize async database manager.

        Args:
            db_path: Optional database path override
        """
        self.db_path = db_path or (config.get_cache_dir() / "ca-bhfuil.db")
        self.sync_manager = schema.DatabaseManager(self.db_path)
        self._executor: concurrent.futures.ThreadPoolExecutor | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        logger.debug(f"Initialized async database manager with {self.db_path}")

    async def initialize(self, max_workers: int = 4) -> None:
        """Initialize the executor and event loop.

        Args:
            max_workers: Maximum number of worker threads
        """
        if not self._executor:
            self._executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers
            )
            self._loop = asyncio.get_event_loop()
            logger.debug(f"Initialized database executor with {max_workers} workers")

    async def shutdown(self) -> None:
        """Shutdown the executor."""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
            self._loop = None
            logger.debug("Database executor shutdown")

    async def run_in_executor(
        self, func: typing.Callable[[], typing.Any]
    ) -> typing.Any:
        """Run a synchronous database operation in executor.

        Args:
            func: Function to run in executor

        Returns:
            Function result
        """
        if not self._executor:
            await self.initialize()

        if not self._loop:
            self._loop = asyncio.get_event_loop()

        try:
            return await self._loop.run_in_executor(self._executor, func)
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise

    async def add_repository(self, path: str, name: str) -> int:
        """Add a repository to the database asynchronously.

        Args:
            path: Repository path
            name: Repository name

        Returns:
            Repository ID
        """
        result = await self.run_in_executor(
            lambda: self.sync_manager.add_repository(path, name)
        )
        return typing.cast("int", result)

    async def get_repository(self, path: str) -> dict[str, typing.Any] | None:
        """Get repository by path asynchronously.

        Args:
            path: Repository path

        Returns:
            Repository data or None
        """
        result = await self.run_in_executor(
            lambda: self.sync_manager.get_repository(path)
        )
        return typing.cast("dict[str, typing.Any] | None", result)

    async def update_repository_stats(
        self, repo_id: int, commit_count: int, branch_count: int
    ) -> None:
        """Update repository statistics asynchronously.

        Args:
            repo_id: Repository ID
            commit_count: Number of commits
            branch_count: Number of branches
        """
        await self.run_in_executor(
            lambda: self.sync_manager.update_repository_stats(
                repo_id, commit_count, branch_count
            )
        )

    async def add_commit(
        self, repository_id: int, commit_data: dict[str, typing.Any]
    ) -> int:
        """Add a commit to the database asynchronously.

        Args:
            repository_id: Repository ID
            commit_data: Commit information

        Returns:
            Commit ID
        """
        result = await self.run_in_executor(
            lambda: self.sync_manager.add_commit(repository_id, commit_data)
        )
        return typing.cast("int", result)

    async def find_commits(
        self,
        repository_id: int,
        sha_pattern: str | None = None,
        message_pattern: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, typing.Any]]:
        """Find commits matching criteria asynchronously.

        Args:
            repository_id: Repository ID
            sha_pattern: SHA pattern to match
            message_pattern: Message pattern to match
            limit: Maximum results

        Returns:
            List of matching commits
        """
        result = await self.run_in_executor(
            lambda: self.sync_manager.find_commits(
                repository_id, sha_pattern, message_pattern, limit
            )
        )
        return typing.cast("list[dict[str, typing.Any]]", result)

    async def get_stats(self) -> dict[str, typing.Any]:
        """Get database statistics asynchronously.

        Returns:
            Database statistics
        """
        result = await self.run_in_executor(lambda: self.sync_manager.get_stats())
        return typing.cast("dict[str, typing.Any]", result)


# Global async database manager instance
_async_db_manager: AsyncDatabaseManager | None = None


async def get_async_database_manager() -> AsyncDatabaseManager:
    """Get the global async database manager instance."""
    global _async_db_manager
    if _async_db_manager is None:
        _async_db_manager = AsyncDatabaseManager()
        await _async_db_manager.initialize()
    return _async_db_manager
