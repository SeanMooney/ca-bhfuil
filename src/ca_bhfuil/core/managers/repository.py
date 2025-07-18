"""Repository manager for orchestrating git operations and database persistence."""

import pathlib
import typing

from loguru import logger
import pygit2
import sqlalchemy.ext.asyncio

from ca_bhfuil.core.git import repository as git_repository
from ca_bhfuil.core.managers import base as base_manager
from ca_bhfuil.core.models import commit as commit_models
from ca_bhfuil.core.models import results as result_models
from ca_bhfuil.storage.database import models as db_models
from ca_bhfuil.storage.database import repository as db_repository


class RepositoryAnalysisResult(result_models.OperationResult):
    """Result of repository analysis with business-specific analytics."""

    repository_path: str | None = None
    commit_count: int = 0
    branch_count: int = 0
    recent_commits: list[commit_models.CommitInfo] = []
    high_impact_commits: list[commit_models.CommitInfo] = []
    authors: list[str] = []
    date_range: dict[str, str] = {}


class CommitSearchResult(result_models.OperationResult):
    """Result of commit search with relevance scoring and pagination."""

    commits: list[commit_models.CommitInfo] = []
    total_count: int = 0
    search_pattern: str = ""
    repository_path: str | None = None


class RepositoryManager(base_manager.BaseManager):
    """Manager for orchestrating repository operations between git and database layers."""

    def __init__(
        self,
        repository_path: pathlib.Path | str,
        db_session: sqlalchemy.ext.asyncio.AsyncSession | None = None,
        db_manager: typing.Any = None,
    ):
        """Initialize repository manager.

        Args:
            repository_path: Path to the git repository
            db_session: Optional database session (creates new if None)
            db_manager: Optional database manager (creates new if None)
        """
        # Import here to avoid circular imports

        super().__init__(db_session, db_manager)
        self.repository_path = pathlib.Path(repository_path)
        self._git_repo = git_repository.Repository(self.repository_path)

    async def load_commits(
        self, from_cache: bool = True, limit: int = 100
    ) -> list[commit_models.CommitInfo]:
        """Load commits with optional caching strategy.

        Args:
            from_cache: Whether to load from database cache first
            limit: Maximum number of commits to return

        Returns:
            List of CommitInfo business models
        """
        if from_cache:
            # Try to load from database cache
            async with self._database_session() as session:
                db_repo = db_repository.DatabaseRepository(session)

                # Try to get repository from database
                db_repository_record = await db_repo.repositories.get_by_path(
                    str(self.repository_path)
                )

                if db_repository_record and db_repository_record.id is not None:
                    # Load commits from database
                    db_commits = await db_repo.commits.get_by_repository(
                        db_repository_record.id, limit=limit
                    )
                    logger.debug(
                        f"Loaded {len(db_commits)} commits from database cache for {self.repository_path}"
                    )
                    return [
                        commit_models.CommitInfo.from_db_model(c) for c in db_commits
                    ]

        # Load from git and optionally cache
        logger.debug(f"Loading commits from git for {self.repository_path}")
        git_commits = self._load_commits_from_git(limit)

        if from_cache:
            # Store in database for future caching
            await self._cache_commits_to_database(git_commits)

        return git_commits

    def _search_all_commits_from_git(
        self, pattern: str
    ) -> list[commit_models.CommitInfo]:
        """Search all commits in git history matching a pattern.

        Args:
            pattern: Pattern to search for in commit messages, authors, etc.

        Returns:
            List of CommitInfo models that match the pattern
        """
        # Use the existing git repository wrapper to search commits
        try:
            if self._git_repo.head_is_unborn:
                return []

            # Walk through all commits from HEAD, no artificial limits
            matching_commits = []
            for commit in self._git_repo._repo.walk(self._git_repo._repo.head.target):
                commit_info = self._git_repo._commit_to_model(commit)
                if commit_info.matches_pattern(pattern):
                    matching_commits.append(commit_info)

            return matching_commits

        except (pygit2.GitError, RuntimeError) as e:
            logger.error(f"Git repository error during search: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching git history: {e}")
            return []

    async def search_commits(
        self, pattern: str, limit: int = 100
    ) -> CommitSearchResult:
        """Search commits with pattern matching and relevance scoring.

        Args:
            pattern: Search pattern to match against
            limit: Maximum number of results

        Returns:
            CommitSearchResult with matched commits and metadata
        """
        async with self._operation_context(
            f"search commits with pattern '{pattern}'"
        ) as (start_time, db_repo):
            try:
                # First, try to search in database cache (limited scope)
                db_commits = await self.load_commits(from_cache=True, limit=1000)
                logger.debug(f"Loaded {len(db_commits)} commits from database cache")

                # Search in database cache
                db_matching_commits = [
                    commit for commit in db_commits if commit.matches_pattern(pattern)
                ]
                logger.debug(
                    f"Found {len(db_matching_commits)} matching commits in database cache"
                )

                # If we have enough matches from database, use them
                if len(db_matching_commits) >= limit:
                    # Sort by impact score (highest first) and limit results
                    db_matching_commits.sort(
                        key=lambda c: c.calculate_impact_score(), reverse=True
                    )
                    limited_commits = db_matching_commits[:limit]

                    return self._create_success_result(
                        CommitSearchResult,
                        start_time,
                        commits=limited_commits,
                        total_count=len(db_matching_commits),
                        search_pattern=pattern,
                        repository_path=str(self.repository_path),
                    )

                # If database search doesn't have enough results, search entire git history
                logger.debug(
                    "Database cache insufficient, searching entire git history"
                )
                all_matching_commits = self._search_all_commits_from_git(pattern)
                logger.debug(
                    f"Found {len(all_matching_commits)} matching commits in full git history"
                )

                # Sort by impact score (highest first) and limit results
                all_matching_commits.sort(
                    key=lambda c: c.calculate_impact_score(), reverse=True
                )
                limited_commits = all_matching_commits[:limit]

                return self._create_success_result(
                    CommitSearchResult,
                    start_time,
                    commits=limited_commits,
                    total_count=len(all_matching_commits),
                    search_pattern=pattern,
                    repository_path=str(self.repository_path),
                )

            except Exception as e:
                return self._create_error_result(
                    CommitSearchResult,
                    start_time,
                    e,
                    search_pattern=pattern,
                    repository_path=str(self.repository_path),
                )

    async def analyze_repository(self) -> RepositoryAnalysisResult:
        """Analyze repository and return business analytics.

        Returns:
            RepositoryAnalysisResult with comprehensive analytics
        """
        async with self._operation_context(
            f"analyze repository {self.repository_path}"
        ) as (start_time, db_repo):
            try:
                # Load commits for analysis
                commits = await self.load_commits(from_cache=True, limit=1000)

                if not commits:
                    return self._create_success_result(
                        RepositoryAnalysisResult,
                        start_time,
                        repository_path=str(self.repository_path),
                        commit_count=0,
                        branch_count=0,
                    )

                # Calculate analytics
                high_impact_commits = [
                    commit
                    for commit in commits
                    if commit.calculate_impact_score() > 0.7
                ]

                # Get unique authors
                authors = list({commit.author_name for commit in commits})

                # Calculate date range
                dates = [commit.author_date for commit in commits]
                date_range = {
                    "earliest": min(dates).isoformat(),
                    "latest": max(dates).isoformat(),
                }

                # Get git statistics for branch count
                git_stats = self._git_repo.get_repository_stats()
                branch_count = git_stats.get("total_branches", 0)

                return self._create_success_result(
                    RepositoryAnalysisResult,
                    start_time,
                    repository_path=str(self.repository_path),
                    commit_count=len(commits),
                    branch_count=branch_count,
                    recent_commits=commits[:10],  # Most recent 10
                    high_impact_commits=high_impact_commits,
                    authors=authors,
                    date_range=date_range,
                )

            except Exception as e:
                return self._create_error_result(
                    RepositoryAnalysisResult,
                    start_time,
                    e,
                    repository_path=str(self.repository_path),
                )

    async def sync_with_database(self) -> None:
        """Synchronize repository data with database.

        This method loads fresh data from git and updates the database cache.
        """
        try:
            async with self._database_session() as session:
                db_repo = db_repository.DatabaseRepository(session)

                # Ensure repository exists in database
                db_repository_record = await db_repo.repositories.get_by_path(
                    str(self.repository_path)
                )

                if not db_repository_record:
                    # Create repository record
                    repo_name = self.repository_path.name
                    repo_create = db_models.RepositoryCreate(
                        path=str(self.repository_path), name=repo_name
                    )
                    db_repository_record = await db_repo.repositories.create(
                        repo_create
                    )
                    logger.info(f"Created repository record for {self.repository_path}")

                # Get repository ID and ensure it's valid
                repository_id = db_repository_record.id
                if repository_id is None:
                    raise RuntimeError("Repository ID is None after creation/retrieval")

                # Load fresh commits from git
                git_commits = self._load_commits_from_git(limit=1000)

                # Sync commits to database
                synced_count = 0
                for commit in git_commits:
                    # Check if commit already exists
                    existing = await db_repo.commits.get_by_sha(
                        repository_id, commit.sha
                    )
                    if not existing:
                        # Create new commit record
                        commit_create = commit.to_db_create(repository_id)
                        await db_repo.commits.create(commit_create)
                        synced_count += 1

                # Update repository statistics
                git_stats = self._git_repo.get_repository_stats()
                await db_repo.repositories.update_stats(
                    repository_id,
                    commit_count=len(git_commits),
                    branch_count=git_stats.get("total_branches", 0),
                )

                logger.info(
                    f"Synced {synced_count} new commits for {self.repository_path}"
                )

        except Exception as e:
            logger.error(f"Database sync failed for {self.repository_path}: {e}")
            raise

    def _load_commits_from_git(self, limit: int) -> list[commit_models.CommitInfo]:
        """Load commits directly from git repository.

        Args:
            limit: Maximum number of commits to load

        Returns:
            List of CommitInfo models from git
        """
        # Use the existing git repository wrapper to get commits
        try:
            if self._git_repo.head_is_unborn:
                return []

            # Walk through commits from HEAD
            commits = []
            for commit in self._git_repo._repo.walk(self._git_repo._repo.head.target):
                commit_info = self._git_repo._commit_to_model(commit)
                commits.append(commit_info)
                if len(commits) >= limit:
                    break

            return commits

        except Exception as e:
            logger.error(f"Failed to load commits from git: {e}")
            return []

    async def _cache_commits_to_database(
        self, commits: list[commit_models.CommitInfo]
    ) -> None:
        """Cache commits to database for future use.

        Args:
            commits: List of CommitInfo models to cache
        """
        if not commits:
            return

        try:
            async with self._database_session() as session:
                db_repo = db_repository.DatabaseRepository(session)

                # Ensure repository exists in database
                db_repository_record = await db_repo.repositories.get_by_path(
                    str(self.repository_path)
                )

                if not db_repository_record:
                    # Create repository record
                    repo_name = self.repository_path.name
                    repo_create = db_models.RepositoryCreate(
                        path=str(self.repository_path), name=repo_name
                    )
                    db_repository_record = await db_repo.repositories.create(
                        repo_create
                    )

                # Get repository ID and ensure it's valid
                repository_id = db_repository_record.id
                if repository_id is None:
                    logger.error("Repository ID is None, cannot cache commits")
                    return

                # Cache commits
                cached_count = 0
                for commit in commits:
                    # Check if commit already exists
                    existing = await db_repo.commits.get_by_sha(
                        repository_id, commit.sha
                    )
                    if not existing:
                        commit_create = commit.to_db_create(repository_id)
                        await db_repo.commits.create(commit_create)
                        cached_count += 1

                logger.debug(f"Cached {cached_count} commits to database")

        except Exception as e:
            logger.error(f"Failed to cache commits to database: {e}")

