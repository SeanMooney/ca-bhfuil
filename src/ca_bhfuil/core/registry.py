"""Repository registry for tracking and managing git repositories."""

import pathlib
import typing

from loguru import logger

from ca_bhfuil.core import config
from ca_bhfuil.core.models import commit as commit_models
from ca_bhfuil.storage.database import schema


class RepositoryRegistry:
    """Registry for managing repository state and tracking."""

    def __init__(
        self,
        config_manager: config.ConfigManager | None = None,
        db_manager: schema.DatabaseManager | None = None,
    ) -> None:
        """Initialize repository registry.

        Args:
            config_manager: Configuration manager instance
            db_manager: Database manager instance
        """
        self.config_manager = config_manager or config.get_config_manager()
        self.db_manager = db_manager or schema.get_database_manager()
        logger.debug("Initialized repository registry")

    def register_repository(self, repo_config: config.RepositoryConfig) -> int:
        """Register a repository in the registry.

        Args:
            repo_config: Repository configuration

        Returns:
            Repository database ID
        """
        repo_path_str = str(repo_config.repo_path)
        logger.info(f"Registering repository: {repo_config.name} at {repo_path_str}")

        # Add to database
        repo_id = self.db_manager.add_repository(
            path=repo_path_str,
            name=repo_config.name,
        )

        logger.debug(f"Repository {repo_config.name} registered with ID {repo_id}")
        return repo_id

    def get_repository_state(self, repo_name: str) -> dict[str, typing.Any] | None:
        """Get repository state by name.

        Args:
            repo_name: Repository name

        Returns:
            Repository state information or None if not found
        """
        # Get repository configuration
        repo_config = self.config_manager.get_repository_config_by_name(repo_name)
        if not repo_config:
            logger.debug(f"Repository configuration not found: {repo_name}")
            return None

        # Get database state
        repo_path_str = str(repo_config.repo_path)
        db_state = self.db_manager.get_repository(repo_path_str)

        if db_state:
            # Merge configuration and database state
            return {
                **db_state,
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

    def list_repositories(self) -> list[dict[str, typing.Any]]:
        """List all repositories with their state.

        Returns:
            List of repository state information
        """
        global_config = self.config_manager.load_configuration()
        repositories = []

        for repo_config in global_config.repos:
            state = self.get_repository_state(repo_config.name)
            if state:
                repositories.append(state)

        return repositories

    def update_repository_stats(
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
        repo_config = self.config_manager.get_repository_config_by_name(repo_name)
        if not repo_config:
            logger.warning(f"Repository configuration not found: {repo_name}")
            return False

        repo_path_str = str(repo_config.repo_path)
        db_state = self.db_manager.get_repository(repo_path_str)

        if db_state:
            repo_id = db_state["id"]
            self.db_manager.update_repository_stats(repo_id, commit_count, branch_count)
            logger.debug(
                f"Updated stats for {repo_name}: {commit_count} commits, {branch_count} branches"
            )
            return True
        logger.warning(f"Repository {repo_name} not found in database")
        return False

    def add_commit(self, repo_name: str, commit_info: commit_models.CommitInfo) -> bool:
        """Add a commit to the repository registry.

        Args:
            repo_name: Repository name
            commit_info: Commit information

        Returns:
            True if added successfully
        """
        repo_config = self.config_manager.get_repository_config_by_name(repo_name)
        if not repo_config:
            logger.warning(f"Repository configuration not found: {repo_name}")
            return False

        repo_path_str = str(repo_config.repo_path)
        db_state = self.db_manager.get_repository(repo_path_str)

        if not db_state:
            # Register repository first
            repo_id = self.register_repository(repo_config)
        else:
            repo_id = db_state["id"]

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
            self.db_manager.add_commit(repo_id, commit_data)
            logger.debug(
                f"Added commit {commit_info.short_sha} to repository {repo_name}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add commit {commit_info.short_sha}: {e}")
            return False

    def search_commits(
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
        repo_config = self.config_manager.get_repository_config_by_name(repo_name)
        if not repo_config:
            logger.warning(f"Repository configuration not found: {repo_name}")
            return []

        repo_path_str = str(repo_config.repo_path)
        db_state = self.db_manager.get_repository(repo_path_str)

        if not db_state:
            logger.debug(f"Repository {repo_name} not found in database")
            return []

        repo_id = db_state["id"]
        commit_data_list = self.db_manager.find_commits(
            repo_id, sha_pattern, message_pattern, limit
        )

        # Convert database results to CommitInfo models
        commits = []
        for commit_data in commit_data_list:
            try:
                commit_info = commit_models.CommitInfo(
                    sha=commit_data["sha"],
                    short_sha=commit_data["short_sha"],
                    message=commit_data["message"],
                    author_name=commit_data["author_name"],
                    author_email=commit_data["author_email"],
                    author_date=commit_data["author_date"],
                    committer_name=commit_data["committer_name"],
                    committer_email=commit_data["committer_email"],
                    committer_date=commit_data["committer_date"],
                    parents=[],  # Not stored in simple schema
                    files_changed=commit_data.get("files_changed"),
                    insertions=commit_data.get("insertions"),
                    deletions=commit_data.get("deletions"),
                )
                commits.append(commit_info)
            except Exception as e:
                logger.warning(f"Failed to parse commit data: {e}")
                continue

        return commits

    def get_registry_stats(self) -> dict[str, typing.Any]:
        """Get registry statistics.

        Returns:
            Registry statistics
        """
        db_stats = self.db_manager.get_stats()
        config_stats = self.config_manager.load_configuration()

        return {
            "configured_repositories": len(config_stats.repos),
            "registered_repositories": db_stats["repositories"],
            "total_commits": db_stats["commits"],
            "total_branches": db_stats["branches"],
            "database_path": db_stats["database_path"],
        }

    def sync_repository_state(self, repo_name: str) -> dict[str, typing.Any]:
        """Synchronize repository state with filesystem.

        Args:
            repo_name: Repository name

        Returns:
            Synchronization result
        """
        repo_state = self.get_repository_state(repo_name)
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
            self.register_repository(config_obj)

        return {
            "success": True,
            "repository": repo_config["name"],
            "exists": exists,
            "is_git_repo": is_git_repo,
            "registered": repo_state.get("registered", True),
        }


# Global registry instance
_repository_registry: RepositoryRegistry | None = None


def get_repository_registry() -> RepositoryRegistry:
    """Get the global repository registry instance."""
    global _repository_registry
    if _repository_registry is None:
        _repository_registry = RepositoryRegistry()
    return _repository_registry
