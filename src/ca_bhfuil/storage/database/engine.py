"""Database engine and session management for SQLModel."""

import contextlib
import pathlib
import typing

from loguru import logger
import sqlalchemy
import sqlalchemy.ext.asyncio
import sqlmodel

from ca_bhfuil.core import config


class DatabaseEngine:
    """Manages SQLAlchemy engine and session creation for SQLModel."""

    def __init__(self, db_path: pathlib.Path | None = None):
        """Initialize database engine.

        Args:
            db_path: Optional database path override
        """
        state_dir = config.get_state_dir()
        self.db_path = db_path or (state_dir / "ca-bhfuil.db")

        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create database URL
        self.database_url = f"sqlite+aiosqlite:///{self.db_path}"

        # Initialize engines
        self._engine: sqlalchemy.ext.asyncio.AsyncEngine | None = None
        self._sync_engine: sqlalchemy.Engine | None = None

        logger.debug(f"Initialized database engine for {self.db_path}")

    @property
    def engine(self) -> sqlalchemy.ext.asyncio.AsyncEngine:
        """Get async SQLAlchemy engine."""
        if self._engine is None:
            self._engine = sqlalchemy.ext.asyncio.create_async_engine(
                self.database_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 30,
                },
            )
            logger.debug("Created async SQLAlchemy engine")
        return self._engine

    @property
    def sync_engine(self) -> sqlalchemy.Engine:
        """Get sync SQLAlchemy engine for schema creation."""
        if self._sync_engine is None:
            sync_url = f"sqlite:///{self.db_path}"
            self._sync_engine = sqlalchemy.create_engine(
                sync_url,
                echo=False,
                pool_pre_ping=True,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 30,
                },
            )
            logger.debug("Created sync SQLAlchemy engine")
        return self._sync_engine

    async def create_tables(self) -> None:
        """Create all database tables."""
        # Use sync engine for table creation as it's more reliable
        sqlmodel.SQLModel.metadata.create_all(self.sync_engine)
        logger.info("Created database tables")

    async def drop_tables(self) -> None:
        """Drop all database tables."""
        # Use sync engine for table operations
        sqlmodel.SQLModel.metadata.drop_all(self.sync_engine)
        logger.warning("Dropped all database tables")

    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            logger.debug("Closed async database engine")

        if self._sync_engine:
            self._sync_engine.dispose()
            self._sync_engine = None
            logger.debug("Closed sync database engine")

    @contextlib.asynccontextmanager
    async def get_session(
        self,
    ) -> typing.AsyncIterator[sqlalchemy.ext.asyncio.AsyncSession]:
        """Get async database session context manager."""
        async with sqlalchemy.ext.asyncio.AsyncSession(
            self.engine, expire_on_commit=False
        ) as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global database engine instance
_db_engine: DatabaseEngine | None = None


def get_database_engine(db_path: pathlib.Path | None = None) -> DatabaseEngine:
    """Get the global database engine instance.

    Args:
        db_path: Optional database path override

    Returns:
        Database engine instance
    """
    global _db_engine
    if _db_engine is None:
        _db_engine = DatabaseEngine(db_path)
    return _db_engine


async def initialize_database(db_path: pathlib.Path | None = None) -> None:
    """Initialize the database with tables.

    Args:
        db_path: Optional database path override
    """
    engine = get_database_engine(db_path)
    await engine.create_tables()
    logger.info("Database initialized successfully")


@contextlib.asynccontextmanager
async def get_db_session(
    db_path: pathlib.Path | None = None,
) -> typing.AsyncIterator[sqlalchemy.ext.asyncio.AsyncSession]:
    """Convenience function to get database session.

    Args:
        db_path: Optional database path override

    Yields:
        Database session
    """
    engine = get_database_engine(db_path)
    async with engine.get_session() as session:
        yield session
