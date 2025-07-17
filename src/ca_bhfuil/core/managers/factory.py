"""Manager factory for creating and configuring managers with proper dependencies."""

import pathlib
import typing

from loguru import logger

from ca_bhfuil.core.managers import base as base_manager
from ca_bhfuil.core.managers import repository as repository_manager
from ca_bhfuil.storage import sqlmodel_manager


class ManagerFactory:
    """Factory for creating managers with proper dependency injection."""

    def __init__(
        self,
        db_path: pathlib.Path | None = None,
        shared_session: bool = True,
    ):
        """Initialize manager factory.

        Args:
            db_path: Optional database path override
            shared_session: Whether to use shared database session across managers
        """
        self._db_path = db_path
        self._shared_session = shared_session
        self._registry = base_manager.ManagerRegistry()
        self._db_manager: sqlmodel_manager.SQLModelDatabaseManager | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the factory and shared database manager."""
        if self._initialized:
            return

        # Create and initialize database manager
        self._db_manager = sqlmodel_manager.SQLModelDatabaseManager(self._db_path)
        await self._db_manager.initialize()

        # Set up shared database manager
        await self._registry.set_shared_database_manager(self._db_manager)

        self._initialized = True
        logger.debug(
            f"Initialized manager factory with database at {self._db_manager.engine.db_path}"
        )

    async def get_repository_manager(
        self,
        repository_path: pathlib.Path | str,
    ) -> repository_manager.RepositoryManager:
        """Get a repository manager for the specified path.

        Args:
            repository_path: Path to the git repository

        Returns:
            Configured RepositoryManager instance
        """
        await self.initialize()

        # Create repository manager with shared dependencies
        repo_manager = repository_manager.RepositoryManager(
            repository_path=repository_path,
            db_manager=self._db_manager,
        )

        # Register with registry for tracking
        manager_key = f"repository:{repository_path}"
        self._registry.register(type(manager_key), repo_manager)

        return repo_manager

    async def get_registry(self) -> base_manager.ManagerRegistry:
        """Get the manager registry for advanced usage.

        Returns:
            Configured ManagerRegistry instance
        """
        await self.initialize()
        return self._registry

    async def close(self) -> None:
        """Close all managers and clean up resources."""
        if self._registry:
            await self._registry.close_all()

        if self._db_manager:
            await self._db_manager.close()
            self._db_manager = None

        self._initialized = False
        logger.debug("Closed manager factory and all resources")

    async def __aenter__(self) -> "ManagerFactory":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: typing.Any,
    ) -> None:
        """Async context manager exit."""
        await self.close()


# Global factory instance for convenience
_global_factory: ManagerFactory | None = None


async def get_manager_factory(
    db_path: pathlib.Path | None = None,
    shared_session: bool = True,
) -> ManagerFactory:
    """Get the global manager factory, creating if needed.

    Args:
        db_path: Optional database path override
        shared_session: Whether to use shared database session across managers

    Returns:
        Configured ManagerFactory instance
    """
    global _global_factory

    if _global_factory is None:
        _global_factory = ManagerFactory(db_path, shared_session)
        await _global_factory.initialize()

    return _global_factory


async def close_global_factory() -> None:
    """Close the global manager factory and clean up resources."""
    global _global_factory

    if _global_factory:
        await _global_factory.close()
        _global_factory = None


# Convenience functions for direct manager access
async def get_repository_manager(
    repository_path: pathlib.Path | str,
    db_path: pathlib.Path | None = None,
) -> repository_manager.RepositoryManager:
    """Get a repository manager with default configuration.

    Args:
        repository_path: Path to the git repository
        db_path: Optional database path override

    Returns:
        Configured RepositoryManager instance
    """
    factory = await get_manager_factory(db_path)
    return await factory.get_repository_manager(repository_path)
