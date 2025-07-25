"""Base manager class with common patterns and error handling."""

import contextlib
import time
import typing

from loguru import logger
import sqlalchemy.ext.asyncio

from ca_bhfuil.core.models import results as result_models
from ca_bhfuil.storage import sqlmodel_manager
from ca_bhfuil.storage.database import repository as db_repository


# Type variable for generic result types
T = typing.TypeVar("T", bound=result_models.OperationResult)
ManagerKey = str


class BaseManager:
    """Base class for all manager implementations.

    Provides common patterns for:
    - Database session management
    - Error handling and logging
    - Operation timing and result creation
    - Resource cleanup
    """

    def __init__(
        self,
        db_session: sqlalchemy.ext.asyncio.AsyncSession | None = None,
        db_manager: sqlmodel_manager.SQLModelDatabaseManager | None = None,
    ):
        """Initialize base manager.

        Args:
            db_session: Optional database session (creates new if None)
            db_manager: Optional database manager (creates new if None)
        """
        self._db_session = db_session
        self._db_manager = db_manager
        self._db_repository: db_repository.DatabaseRepository | None = None
        self._session_owned = db_session is None
        self._manager_owned = db_manager is None

    @contextlib.asynccontextmanager
    async def _database_session(
        self,
    ) -> typing.AsyncIterator[sqlalchemy.ext.asyncio.AsyncSession]:
        """Context manager for database sessions.

        Yields:
            Database session for operations
        """
        if self._db_session is not None:
            # Use existing session
            yield self._db_session
        else:
            # Create new session with proper context management
            db_manager = await self._get_db_manager()
            async with db_manager.engine.get_session() as session:
                yield session

    async def _get_db_repository(self) -> db_repository.DatabaseRepository:
        """Get database repository, creating session if needed."""
        if self._db_repository is None:
            if self._db_session is None:
                # This should not be called directly anymore - use _database_session context manager
                raise RuntimeError(
                    "Cannot get repository without session. Use _database_session context manager."
                )
            self._db_repository = db_repository.DatabaseRepository(self._db_session)
        return self._db_repository

    async def _get_db_manager(self) -> sqlmodel_manager.SQLModelDatabaseManager:
        """Get database manager, creating if needed."""
        if self._db_manager is None:
            self._db_manager = sqlmodel_manager.SQLModelDatabaseManager()
            await self._db_manager.initialize()
        return self._db_manager

    @contextlib.asynccontextmanager
    async def _operation_context(
        self, operation_name: str
    ) -> typing.AsyncIterator[tuple[float, db_repository.DatabaseRepository]]:
        """Context manager for operations with timing and error handling.

        Args:
            operation_name: Name of the operation for logging

        Yields:
            tuple[start_time, db_repository]: Start time and database repository
        """
        start_time = time.perf_counter()
        logger.debug(f"Starting {operation_name}")

        try:
            async with self._database_session() as session:
                db_repo = db_repository.DatabaseRepository(session)
                yield start_time, db_repo

        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(f"{operation_name} failed after {duration:.3f}s: {e}")
            raise

        else:
            duration = time.perf_counter() - start_time
            logger.debug(f"{operation_name} completed in {duration:.3f}s")

    def _create_success_result(
        self,
        result_type: type[T],
        start_time: float,
        **kwargs: typing.Any,
    ) -> T:
        """Create a successful operation result.

        Args:
            result_type: Type of result to create
            start_time: When the operation started
            **kwargs: Additional fields for the result

        Returns:
            Success result with calculated duration
        """
        duration = time.perf_counter() - start_time
        return result_type(
            success=True,
            duration=duration,
            **kwargs,
        )

    def _create_error_result(
        self,
        result_type: type[T],
        start_time: float,
        error: Exception,
        **kwargs: typing.Any,
    ) -> T:
        """Create an error operation result.

        Args:
            result_type: Type of result to create
            start_time: When the operation started
            error: The exception that occurred
            **kwargs: Additional fields for the result

        Returns:
            Error result with calculated duration and error message
        """
        duration = time.perf_counter() - start_time
        return result_type(
            success=False,
            duration=duration,
            error=str(error),
            **kwargs,
        )

    @contextlib.asynccontextmanager
    async def _transaction(
        self,
    ) -> typing.AsyncIterator[sqlalchemy.ext.asyncio.AsyncSession]:
        """Context manager for database transactions.

        Yields:
            Database session with transaction management
        """
        async with self._database_session() as session:
            try:
                yield session
                await session.commit()

            except Exception:
                await session.rollback()
                raise

    async def close(self) -> None:
        """Close database connections and clean up resources."""
        # Clear session references (actual cleanup handled by context managers)
        self._db_session = None
        self._db_repository = None

        # Close database manager if we own it
        if self._manager_owned and self._db_manager:
            await self._db_manager.close()
            self._db_manager = None


class ManagerRegistry:
    """Registry for managing dependencies between managers."""

    def __init__(self) -> None:
        """Initialize empty manager registry."""
        self._managers: dict[ManagerKey, typing.Any] = {}
        self._db_session: sqlalchemy.ext.asyncio.AsyncSession | None = None
        self._db_manager: sqlmodel_manager.SQLModelDatabaseManager | None = None

    def register(self, manager_key: ManagerKey, manager_instance: typing.Any) -> None:
        """Register a manager instance.

        Args:
            manager_key: String key for instance-specific tracking
            manager_instance: The manager instance to register
        """
        self._managers[manager_key] = manager_instance
        logger.debug(f"Registered manager: {manager_key}")

    def get(self, manager_key: ManagerKey) -> typing.Any:
        """Get a registered manager instance.

        Args:
            manager_key: String key of manager to retrieve

        Returns:
            The registered manager instance (use type hints for specific type)

        Raises:
            KeyError: If manager key is not registered

        Note:
            Return type is `typing.Any` to accommodate different manager types.
            Consider using type hints when calling this method to restore type safety:

            ```python
            manager: RepositoryManager = registry.get("repository:/path/to/repo")
            ```
        """
        if manager_key not in self._managers:
            raise KeyError(f"Manager key '{manager_key}' not registered")
        return self._managers[manager_key]

    async def set_shared_database_manager(
        self, db_manager: sqlmodel_manager.SQLModelDatabaseManager
    ) -> None:
        """Set a shared database manager for all managers.

        Args:
            db_manager: Database manager to share across managers
        """
        self._db_manager = db_manager

        # Update existing managers
        for manager in self._managers.values():
            if hasattr(manager, "_db_manager"):
                manager._db_manager = db_manager
                manager._db_repository = None  # Force recreation with new manager

    async def set_shared_session(
        self, session: sqlalchemy.ext.asyncio.AsyncSession
    ) -> None:
        """Set a shared database session for all managers.

        Args:
            session: Database session to share across managers
        """
        self._db_session = session

        # Update existing managers
        for manager in self._managers.values():
            if hasattr(manager, "_db_session"):
                manager._db_session = session
                manager._db_repository = None  # Force recreation with new session

    async def close_all(self) -> None:
        """Close all registered managers."""
        for manager in self._managers.values():
            if hasattr(manager, "close"):
                await manager.close()

        if self._db_session:
            await self._db_session.close()

        if self._db_manager:
            await self._db_manager.close()

        self._managers.clear()
        logger.debug("Closed all managers and cleared registry")
