"""SQLModel-based database manager replacing the old async_database.py."""

import pathlib
import typing

from loguru import logger

from ca_bhfuil.storage.database import engine
from ca_bhfuil.storage.database import models
from ca_bhfuil.storage.database import repository


class SQLModelDatabaseManager:
    """Manages database operations using SQLModel and async SQLAlchemy."""

    def __init__(self, db_path: pathlib.Path | None = None):
        """Initialize SQLModel database manager.

        Args:
            db_path: Optional database path override
        """
        self.engine = engine.get_database_engine(db_path)
        logger.debug(
            f"Initialized SQLModel database manager with {self.engine.db_path}"
        )

    async def initialize(self) -> None:
        """Initialize the database tables."""
        await self.engine.create_tables()
        logger.info("Database tables initialized")

    async def close(self) -> None:
        """Close database connections."""
        await self.engine.close()

    async def add_repository(self, path: str, name: str) -> int:
        """Add a repository to the database.

        Args:
            path: Repository path
            name: Repository name

        Returns:
            Repository ID
        """
        async with self.engine.get_session() as session:
            db_repo = repository.DatabaseRepository(session)

            # Check if repository already exists
            existing = await db_repo.repositories.get_by_path(path)
            if existing:
                return existing.id or 0

            # Create new repository
            repo_data = models.RepositoryCreate(path=path, name=name)
            repo = await db_repo.repositories.create(repo_data)
            return repo.id or 0

    async def get_repository(self, path: str) -> models.RepositoryRead | None:
        """Get repository by path.

        Args:
            path: Repository path

        Returns:
            Repository data or None
        """
        async with self.engine.get_session() as session:
            db_repo = repository.DatabaseRepository(session)
            repo = await db_repo.repositories.get_by_path(path)

            if repo:
                return models.RepositoryRead(
                    id=repo.id or 0,
                    path=repo.path,
                    name=repo.name,
                    last_analyzed=repo.last_analyzed,
                    commit_count=repo.commit_count,
                    branch_count=repo.branch_count,
                    created_at=repo.created_at,
                    updated_at=repo.updated_at,
                )
            return None

    async def update_repository_stats(
        self, repo_id: int, commit_count: int, branch_count: int
    ) -> None:
        """Update repository statistics.

        Args:
            repo_id: Repository ID
            commit_count: Number of commits
            branch_count: Number of branches
        """
        async with self.engine.get_session() as session:
            db_repo = repository.DatabaseRepository(session)
            await db_repo.repositories.update_stats(repo_id, commit_count, branch_count)

    async def add_commit(
        self, repository_id: int, commit_data: dict[str, typing.Any]
    ) -> int:
        """Add a commit to the database.

        Args:
            repository_id: Repository ID
            commit_data: Commit information

        Returns:
            Commit ID
        """
        async with self.engine.get_session() as session:
            db_repo = repository.DatabaseRepository(session)

            # Check if commit already exists
            existing = await db_repo.commits.get_by_sha(
                repository_id, commit_data["sha"]
            )
            if existing:
                return existing.id or 0

            # Create new commit
            commit_create_data = models.CommitCreate(
                repository_id=repository_id,
                sha=commit_data["sha"],
                short_sha=commit_data["short_sha"],
                message=commit_data["message"],
                author_name=commit_data["author_name"],
                author_email=commit_data["author_email"],
                author_date=commit_data["author_date"],
                committer_name=commit_data["committer_name"],
                committer_email=commit_data["committer_email"],
                committer_date=commit_data["committer_date"],
                files_changed=commit_data.get("files_changed"),
                insertions=commit_data.get("insertions"),
                deletions=commit_data.get("deletions"),
            )
            commit = await db_repo.commits.create(commit_create_data)
            return commit.id or 0

    async def find_commits(
        self,
        repository_id: int,
        sha_pattern: str | None = None,
        message_pattern: str | None = None,
        limit: int = 100,
    ) -> list[models.CommitRead]:
        """Find commits matching criteria.

        Args:
            repository_id: Repository ID
            sha_pattern: SHA pattern to match
            message_pattern: Message pattern to match
            limit: Maximum results

        Returns:
            List of matching commits
        """
        async with self.engine.get_session() as session:
            db_repo = repository.DatabaseRepository(session)
            commits = await db_repo.commits.find_commits(
                repository_id, sha_pattern, message_pattern, limit
            )

            return [
                models.CommitRead(
                    id=commit.id or 0,
                    repository_id=commit.repository_id,
                    sha=commit.sha,
                    short_sha=commit.short_sha,
                    message=commit.message,
                    author_name=commit.author_name,
                    author_email=commit.author_email,
                    author_date=commit.author_date,
                    committer_name=commit.committer_name,
                    committer_email=commit.committer_email,
                    committer_date=commit.committer_date,
                    files_changed=commit.files_changed,
                    insertions=commit.insertions,
                    deletions=commit.deletions,
                    created_at=commit.created_at,
                )
                for commit in commits
            ]

    async def get_stats(self) -> dict[str, typing.Any]:
        """Get database statistics.

        Returns:
            Database statistics
        """
        async with self.engine.get_session() as session:
            db_repo = repository.DatabaseRepository(session)
            return await db_repo.get_stats()


# Global SQLModel database manager instance
_sqlmodel_db_manager: SQLModelDatabaseManager | None = None


async def get_sqlmodel_database_manager(
    db_path: pathlib.Path | None = None,
) -> SQLModelDatabaseManager:
    """Get the global SQLModel database manager instance.

    Args:
        db_path: Optional database path override

    Returns:
        SQLModel database manager instance
    """
    global _sqlmodel_db_manager
    if _sqlmodel_db_manager is None:
        _sqlmodel_db_manager = SQLModelDatabaseManager(db_path)
        await _sqlmodel_db_manager.initialize()
    return _sqlmodel_db_manager
