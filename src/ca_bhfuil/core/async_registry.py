"""Async repository registry for tracking and managing git repositories."""

import asyncio
import pathlib
import typing

from loguru import logger

from ca_bhfuil.core import async_config
from ca_bhfuil.core import config
from ca_bhfuil.core.models import commit as commit_models
from ca_bhfuil.storage import sqlmodel_manager


class AsyncRepositoryRegistry:
    """Async registry for managing repository state and tracking."""

    def __init__(
        self,
        config_manager: async_config.AsyncConfigManager | None = None,
        db_manager: sqlmodel_manager.SQLModelDatabaseManager | None = None,
    ) -> None:
        """Initialize async repository registry.

        Args:
            config_manager: Async configuration manager instance
            db_manager: SQLModel database manager instance
        """
        self.config_manager = config_manager or async_config.AsyncConfigManager()
        self.db_manager = db_manager or sqlmodel_manager.SQLModelDatabaseManager()
        self._lock = asyncio.Lock()
        logger.debug("Initialized async repository registry")

    async def register_repository(self, repo_config: config.RepositoryConfig) -> int:
        """Register a repository in the registry.

        Args:
            repo_config: Repository configuration

        Returns:
            Repository database ID
        """
        async with self._lock:
            repo_path_str = str(repo_config.repo_path)
            logger.info(
                f"Registering repository: {repo_config.name} at {repo_path_str}"
            )

            # Add to database using SQLModel
            repo_id = await self.db_manager.add_repository(
                path=repo_path_str,
                name=repo_config.name,
            )

            logger.debug(f"Repository {repo_config.name} registered with ID {repo_id}")
            return repo_id

    async def get_repository_state(
        self, repo_name: str
    ) -> dict[str, typing.Any] | None:
        """Get repository state by name.

        Args:
            repo_name: Repository name

        Returns:
            Repository state information or None if not found
        """
        # Get repository configuration
        repo_config = await self.config_manager.get_repository_config_by_name(repo_name)
        if not repo_config:
            logger.debug(f"Repository configuration not found: {repo_name}")
            return None

        # Get database state
        repo_path_str = str(repo_config.repo_path)
        db_repo = await self.db_manager.get_repository(repo_path_str)

        if db_repo:
            # Merge configuration and database state
            return {
                "id": db_repo.id,
                "path": db_repo.path,
                "name": db_repo.name,
                "last_analyzed": db_repo.last_analyzed,
                "commit_count": db_repo.commit_count,
                "branch_count": db_repo.branch_count,
                "created_at": db_repo.created_at,
                "updated_at": db_repo.updated_at,
                "config": {
                    "name": repo_config.name,
                    "source": repo_config.source,
                    "auth_key": repo_config.auth_key,
                    "repo_path": repo_config.repo_path,
                    "state_path": repo_config.state_path,
                },
                "exists": repo_config.repo_path.exists(),
                "is_git_repo": (repo_config.repo_path / ".git").exists()
                if repo_config.repo_path.exists()
                else False,
                "registered": True,
            }
        # Repository not in database yet
        logger.debug(f"Repository {repo_name} not found in database")
        return {
            "config": {
                "name": repo_config.name,
                "source": repo_config.source,
                "auth_key": repo_config.auth_key,
                "repo_path": repo_config.repo_path,
                "state_path": repo_config.state_path,
            },
            "exists": repo_config.repo_path.exists(),
            "is_git_repo": (repo_config.repo_path / ".git").exists()
            if repo_config.repo_path.exists()
            else False,
            "registered": False,
        }

    async def list_repositories(self) -> list[dict[str, typing.Any]]:
        """List all repositories with their state.

        Returns:
            List of repository state information
        """
        global_config = await self.config_manager.load_configuration()
        repositories = []

        for repo_config in global_config.repos:
            state = await self.get_repository_state(repo_config.name)
            if state:
                repositories.append(state)

        return repositories

    async def update_repository_stats(
        self, repo_name: str, commit_count: int, branch_count: int
    ) -> bool:
        """Update repository statistics.

        Args:
            repo_name: Repository name
            commit_count: Number of commits
            branch_count: Number of branches

        Returns:
            True if updated successfully
        """
        repo_config = await self.config_manager.get_repository_config_by_name(repo_name)
        if not repo_config:
            logger.warning(f"Repository configuration not found: {repo_name}")
            return False

        repo_path_str = str(repo_config.repo_path)
        db_repo = await self.db_manager.get_repository(repo_path_str)

        if db_repo:
            repo_id = db_repo.id or 0
            await self.db_manager.update_repository_stats(
                repo_id, commit_count, branch_count
            )
            logger.debug(
                f"Updated stats for {repo_name}: {commit_count} commits, {branch_count} branches"
            )
            return True
        logger.warning(f"Repository {repo_name} not found in database")
        return False

    async def add_commit(
        self, repo_name: str, commit_info: commit_models.CommitInfo
    ) -> bool:
        """Add a commit to the repository registry.

        Args:
            repo_name: Repository name
            commit_info: Commit information

        Returns:
            True if added successfully
        """
        repo_config = await self.config_manager.get_repository_config_by_name(repo_name)
        if not repo_config:
            logger.warning(f"Repository configuration not found: {repo_name}")
            return False

        repo_path_str = str(repo_config.repo_path)
        db_repo = await self.db_manager.get_repository(repo_path_str)

        if not db_repo:
            # Register repository first
            repo_id = await self.register_repository(repo_config)
        else:
            repo_id = db_repo.id or 0

        # Convert commit info to database format
        commit_data = {
            "sha": commit_info.sha,
            "short_sha": commit_info.short_sha,
            "message": commit_info.message,
            "author_name": commit_info.author_name,
            "author_email": commit_info.author_email,
            "author_date": commit_info.author_date.isoformat(),
            "committer_name": commit_info.committer_name,
            "committer_email": commit_info.committer_email,
            "committer_date": commit_info.committer_date.isoformat(),
            "files_changed": commit_info.files_changed,
            "insertions": commit_info.insertions,
            "deletions": commit_info.deletions,
        }

        try:
            await self.db_manager.add_commit(repo_id, commit_data)
            logger.debug(
                f"Added commit {commit_info.short_sha} to repository {repo_name}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add commit {commit_info.short_sha}: {e}")
            return False

    async def search_commits(
        self,
        repo_name: str,
        sha_pattern: str | None = None,
        message_pattern: str | None = None,
        limit: int = 100,
    ) -> list[commit_models.CommitInfo]:
        """Search commits in a repository.

        Args:
            repo_name: Repository name
            sha_pattern: SHA pattern to match
            message_pattern: Message pattern to match
            limit: Maximum results

        Returns:
            List of matching commits
        """
        repo_config = await self.config_manager.get_repository_config_by_name(repo_name)
        if not repo_config:
            logger.warning(f"Repository configuration not found: {repo_name}")
            return []

        repo_path_str = str(repo_config.repo_path)
        db_repo = await self.db_manager.get_repository(repo_path_str)

        if not db_repo:
            logger.debug(f"Repository {repo_name} not found in database")
            return []

        repo_id = db_repo.id or 0
        commit_data_list = await self.db_manager.find_commits(
            repo_id, sha_pattern, message_pattern, limit
        )

        # Convert database results to CommitInfo models
        commits = []
        for commit_data in commit_data_list:
            try:
                commit_info = commit_models.CommitInfo(
                    sha=commit_data.sha,
                    short_sha=commit_data.short_sha,
                    message=commit_data.message,
                    author_name=commit_data.author_name,
                    author_email=commit_data.author_email,
                    author_date=commit_data.author_date,
                    committer_name=commit_data.committer_name,
                    committer_email=commit_data.committer_email,
                    committer_date=commit_data.committer_date,
                    parents=[],  # Not stored in simple schema
                    files_changed=commit_data.files_changed,
                    insertions=commit_data.insertions,
                    deletions=commit_data.deletions,
                )
                commits.append(commit_info)
            except Exception as e:
                logger.warning(f"Failed to parse commit data: {e}")
                continue

        return commits

    async def get_registry_stats(self) -> dict[str, typing.Any]:
        """Get registry statistics.

        Returns:
            Registry statistics
        """
        db_stats = await self.db_manager.get_stats()
        config_stats = await self.config_manager.load_configuration()

        return {
            "configured_repositories": len(config_stats.repos),
            "registered_repositories": db_stats["repositories"],
            "total_commits": db_stats["commits"],
            "total_branches": db_stats["branches"],
            "database_path": str(self.db_manager.engine.db_path),
        }

    async def sync_repository_state(self, repo_name: str) -> dict[str, typing.Any]:
        """Synchronize repository state with filesystem.

        Args:
            repo_name: Repository name

        Returns:
            Synchronization result
        """
        repo_state = await self.get_repository_state(repo_name)
        if not repo_state:
            return {"success": False, "error": "Repository not found"}

        repo_config = repo_state["config"]
        repo_path = pathlib.Path(repo_config["repo_path"])

        # Check filesystem state
        exists = repo_path.exists()
        is_git_repo = (repo_path / ".git").exists() if exists else False

        # Register if not already registered and exists
        if exists and is_git_repo and not repo_state.get("registered", True):
            config_obj = config.RepositoryConfig(
                name=repo_config["name"],
                source=repo_config["source"],
                auth_key=repo_config.get("auth_key"),
            )
            await self.register_repository(config_obj)

        return {
            "success": True,
            "repository": repo_config["name"],
            "exists": exists,
            "is_git_repo": is_git_repo,
            "registered": repo_state.get("registered", True),
        }


# Global async registry instance
_async_repository_registry: AsyncRepositoryRegistry | None = None


async def get_async_repository_registry() -> AsyncRepositoryRegistry:
    """Get the global async repository registry instance."""
    global _async_repository_registry
    if _async_repository_registry is None:
        _async_repository_registry = AsyncRepositoryRegistry()
    return _async_repository_registry
