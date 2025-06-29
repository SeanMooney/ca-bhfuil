"""Repository pattern implementation using SQLModel."""

import datetime
import typing

from loguru import logger
import sqlalchemy
import sqlalchemy.ext.asyncio
import sqlmodel

from ca_bhfuil.storage.database import engine
from ca_bhfuil.storage.database import models


class BaseRepository:
    """Base repository class with common database operations."""

    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async database session
        """
        self.session = session

    async def save(self, instance: sqlmodel.SQLModel) -> None:
        """Save an instance to the database.

        Args:
            instance: SQLModel instance to save
        """
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)

    async def delete(self, instance: sqlmodel.SQLModel) -> None:
        """Delete an instance from the database.

        Args:
            instance: SQLModel instance to delete
        """
        await self.session.delete(instance)
        await self.session.commit()


class RepositoryRepository(BaseRepository):
    """Repository for managing Repository entities."""

    async def create(self, repo_data: models.RepositoryCreate) -> models.Repository:
        """Create a new repository.

        Args:
            repo_data: Repository creation data

        Returns:
            Created repository
        """
        repo = models.Repository(**repo_data.model_dump())
        await self.save(repo)
        logger.debug(f"Created repository: {repo.path}")
        return repo

    async def get_by_path(self, path: str) -> models.Repository | None:
        """Get repository by path.

        Args:
            path: Repository path

        Returns:
            Repository or None if not found
        """
        statement = sqlmodel.select(models.Repository).where(
            models.Repository.path == path
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id(self, repo_id: int) -> models.Repository | None:
        """Get repository by ID.

        Args:
            repo_id: Repository ID

        Returns:
            Repository or None if not found
        """
        return await self.session.get(models.Repository, repo_id)

    async def update_stats(
        self, repo_id: int, commit_count: int, branch_count: int
    ) -> models.Repository | None:
        """Update repository statistics.

        Args:
            repo_id: Repository ID
            commit_count: Number of commits
            branch_count: Number of branches

        Returns:
            Updated repository or None if not found
        """
        repo = await self.get_by_id(repo_id)
        if repo:
            repo.commit_count = commit_count
            repo.branch_count = branch_count
            repo.last_analyzed = datetime.datetime.utcnow()
            await self.save(repo)
            logger.debug(f"Updated repository stats: {repo.path}")
        return repo

    async def list_all(self) -> list[models.Repository]:
        """List all repositories.

        Returns:
            List of repositories
        """
        statement = sqlmodel.select(models.Repository)
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class CommitRepository(BaseRepository):
    """Repository for managing Commit entities."""

    async def create(self, commit_data: models.CommitCreate) -> models.Commit:
        """Create a new commit.

        Args:
            commit_data: Commit creation data

        Returns:
            Created commit
        """
        commit = models.Commit(**commit_data.model_dump())
        await self.save(commit)
        logger.debug(f"Created commit: {commit.short_sha}")
        return commit

    async def get_by_sha(self, repository_id: int, sha: str) -> models.Commit | None:
        """Get commit by SHA.

        Args:
            repository_id: Repository ID
            sha: Commit SHA (full or partial)

        Returns:
            Commit or None if not found
        """
        statement = sqlmodel.select(models.Commit).where(
            models.Commit.repository_id == repository_id,
            sqlmodel.or_(
                models.Commit.sha == sha,
                models.Commit.short_sha == sha,
                models.Commit.sha.startswith(sha),
            ),
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def find_commits(
        self,
        repository_id: int,
        sha_pattern: str | None = None,
        message_pattern: str | None = None,
        limit: int = 100,
    ) -> list[models.Commit]:
        """Find commits matching criteria.

        Args:
            repository_id: Repository ID
            sha_pattern: SHA pattern to match
            message_pattern: Message pattern to match
            limit: Maximum results

        Returns:
            List of matching commits
        """
        statement = sqlmodel.select(models.Commit).where(
            models.Commit.repository_id == repository_id
        )

        if sha_pattern:
            statement = statement.where(
                sqlmodel.or_(
                    models.Commit.sha.like(f"%{sha_pattern}%"),  # type: ignore[attr-defined]
                    models.Commit.short_sha.like(f"%{sha_pattern}%"),  # type: ignore[attr-defined]
                )
            )

        if message_pattern:
            statement = statement.where(
                models.Commit.message.like(f"%{message_pattern}%")  # type: ignore[attr-defined]
            )

        statement = statement.order_by(
            sqlalchemy.desc(models.Commit.author_date)
        ).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_repository(
        self, repository_id: int, limit: int = 100
    ) -> list[models.Commit]:
        """Get commits for a repository.

        Args:
            repository_id: Repository ID
            limit: Maximum results

        Returns:
            List of commits
        """
        statement = (
            sqlmodel.select(models.Commit)
            .where(models.Commit.repository_id == repository_id)
            .order_by(sqlalchemy.desc(models.Commit.author_date))
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class BranchRepository(BaseRepository):
    """Repository for managing Branch entities."""

    async def create(self, branch_data: models.BranchCreate) -> models.Branch:
        """Create a new branch.

        Args:
            branch_data: Branch creation data

        Returns:
            Created branch
        """
        branch = models.Branch(**branch_data.model_dump())
        await self.save(branch)
        logger.debug(f"Created branch: {branch.name}")
        return branch

    async def get_by_name(self, repository_id: int, name: str) -> models.Branch | None:
        """Get branch by name.

        Args:
            repository_id: Repository ID
            name: Branch name

        Returns:
            Branch or None if not found
        """
        statement = sqlmodel.select(models.Branch).where(
            models.Branch.repository_id == repository_id,
            models.Branch.name == name,
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_repository(self, repository_id: int) -> list[models.Branch]:
        """Get branches for a repository.

        Args:
            repository_id: Repository ID

        Returns:
            List of branches
        """
        statement = sqlmodel.select(models.Branch).where(
            models.Branch.repository_id == repository_id
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class DatabaseRepository:
    """Main repository class providing access to all sub-repositories."""

    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession):
        """Initialize with database session.

        Args:
            session: Async database session
        """
        self.session = session
        self.repositories = RepositoryRepository(session)
        self.commits = CommitRepository(session)
        self.branches = BranchRepository(session)

    async def get_stats(self) -> dict[str, typing.Any]:
        """Get database statistics.

        Returns:
            Database statistics
        """
        # Count repositories
        repo_statement = sqlmodel.select(sqlmodel.func.count()).select_from(
            models.Repository
        )
        repo_result = await self.session.execute(repo_statement)
        repo_count = repo_result.scalar_one()

        # Count commits
        commit_statement = sqlmodel.select(sqlmodel.func.count()).select_from(
            models.Commit
        )
        commit_result = await self.session.execute(commit_statement)
        commit_count = commit_result.scalar_one()

        # Count branches
        branch_statement = sqlmodel.select(sqlmodel.func.count()).select_from(
            models.Branch
        )
        branch_result = await self.session.execute(branch_statement)
        branch_count = branch_result.scalar_one()

        return {
            "repositories": repo_count,
            "commits": commit_count,
            "branches": branch_count,
            "database_path": str(engine.get_database_engine().db_path),
        }
