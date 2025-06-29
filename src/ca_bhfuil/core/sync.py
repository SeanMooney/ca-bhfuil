"""Repository synchronization for keeping repositories up to date."""

import time
import typing

from loguru import logger
import pygit2

from ca_bhfuil.core import config
from ca_bhfuil.core import registry
from ca_bhfuil.core.git import repository as repository_module
from ca_bhfuil.core.models import results as results_models


class RepositorySynchronizer:
    """Handles synchronization of git repositories."""

    def __init__(
        self,
        config_manager: config.ConfigManager | None = None,
        repo_registry: registry.RepositoryRegistry | None = None,
    ) -> None:
        """Initialize repository synchronizer.

        Args:
            config_manager: Configuration manager instance
            repo_registry: Repository registry instance
        """
        self.config_manager = config_manager or config.get_config_manager()
        self.repo_registry = repo_registry or registry.get_repository_registry()
        logger.debug("Initialized repository synchronizer")

    def sync_repository(self, repo_name: str) -> results_models.OperationResult:
        """Synchronize a single repository.

        Args:
            repo_name: Repository name

        Returns:
            Operation result with sync information
        """
        start_time = time.time()

        try:
            # Get repository configuration
            repo_config = self.config_manager.get_repository_config_by_name(repo_name)
            if not repo_config:
                return results_models.OperationResult(
                    success=False,
                    duration=time.time() - start_time,
                    error=f"Repository '{repo_name}' not found in configuration",
                )

            # Check if repository exists locally
            if not repo_config.repo_path.exists():
                return results_models.OperationResult(
                    success=False,
                    duration=time.time() - start_time,
                    error=f"Repository path does not exist: {repo_config.repo_path}",
                )

            if not (repo_config.repo_path / ".git").exists():
                return results_models.OperationResult(
                    success=False,
                    duration=time.time() - start_time,
                    error=f"Not a git repository: {repo_config.repo_path}",
                )

            # Perform synchronization
            sync_result = self._perform_sync(repo_config)

            # Update registry with latest state
            if sync_result["success"]:
                self._update_registry_after_sync(repo_config, sync_result)

            return results_models.OperationResult(
                success=sync_result["success"],
                duration=time.time() - start_time,
                result=sync_result,
            )

        except Exception as e:
            logger.error(f"Failed to sync repository {repo_name}: {e}")
            return results_models.OperationResult(
                success=False, duration=time.time() - start_time, error=str(e)
            )

    def _perform_sync(
        self, repo_config: config.RepositoryConfig
    ) -> dict[str, typing.Any]:
        """Perform the actual synchronization.

        Args:
            repo_config: Repository configuration

        Returns:
            Sync result dictionary
        """
        try:
            repo = pygit2.Repository(str(repo_config.repo_path))

            # Get remote information
            remote_name = "origin"  # Default remote
            try:
                remote = repo.remotes[remote_name]  # type: ignore[attr-defined]
            except KeyError:
                logger.warning(
                    f"Remote '{remote_name}' not found in {repo_config.name}"
                )
                return {
                    "success": False,
                    "error": f"Remote '{remote_name}' not found",
                }

            # Count refs before fetch
            refs_before = len(repo.listall_branches())
            commits_before = len(list(repo.walk(repo.head.target)))

            # Perform fetch
            logger.info(f"Fetching updates for {repo_config.name}")
            remote.fetch()

            # Count refs after fetch
            refs_after = len(repo.listall_branches())
            commits_after = len(list(repo.walk(repo.head.target)))

            # Calculate changes
            new_refs = refs_after - refs_before
            new_commits = commits_after - commits_before

            logger.info(
                f"Sync complete for {repo_config.name}: "
                f"{new_refs} new refs, {new_commits} new commits"
            )

            return {
                "success": True,
                "repository": repo_config.name,
                "refs_before": refs_before,
                "refs_after": refs_after,
                "new_refs": new_refs,
                "commits_before": commits_before,
                "commits_after": commits_after,
                "new_commits": new_commits,
                "remote": remote_name,
            }

        except pygit2.GitError as e:
            logger.error(f"Git error during sync of {repo_config.name}: {e}")
            return {
                "success": False,
                "error": f"Git error: {e}",
            }
        except Exception as e:
            logger.error(f"Unexpected error during sync of {repo_config.name}: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {e}",
            }

    def _update_registry_after_sync(
        self, repo_config: config.RepositoryConfig, sync_result: dict[str, typing.Any]
    ) -> None:
        """Update repository registry after successful sync.

        Args:
            repo_config: Repository configuration
            sync_result: Sync operation result
        """
        try:
            # Get updated repository statistics
            repo_wrapper = repository_module.Repository(repo_config.repo_path)
            branches = repo_wrapper.list_branches()
            branch_count = len(branches)

            # For commit count, we could walk the entire repository
            # but that's expensive, so we'll use the commits_after count
            commit_count = sync_result.get("commits_after", 0)

            # Update registry stats
            self.repo_registry.update_repository_stats(
                repo_config.name, commit_count, branch_count
            )

            logger.debug(
                f"Updated registry stats for {repo_config.name}: "
                f"{commit_count} commits, {branch_count} branches"
            )

        except Exception as e:
            logger.warning(f"Failed to update registry after sync: {e}")

    def sync_all_repositories(self) -> list[results_models.OperationResult]:
        """Synchronize all configured repositories.

        Returns:
            List of operation results for each repository
        """
        logger.info("Starting synchronization of all repositories")
        start_time = time.time()

        global_config = self.config_manager.load_configuration()
        results = []

        for repo_config in global_config.repos:
            logger.info(f"Synchronizing repository: {repo_config.name}")
            result = self.sync_repository(repo_config.name)
            results.append(result)

            if result.success:
                logger.info(f"✅ {repo_config.name} synchronized successfully")
            else:
                logger.warning(f"❌ {repo_config.name} sync failed: {result.error}")

        total_duration = time.time() - start_time
        successful_syncs = sum(1 for r in results if r.success)
        failed_syncs = len(results) - successful_syncs

        logger.info(
            f"Synchronization complete: {successful_syncs} successful, "
            f"{failed_syncs} failed, {total_duration:.2f}s total"
        )

        return results

    def get_sync_status(self, repo_name: str) -> dict[str, typing.Any]:
        """Get synchronization status for a repository.

        Args:
            repo_name: Repository name

        Returns:
            Sync status information
        """
        try:
            repo_config = self.config_manager.get_repository_config_by_name(repo_name)
            if not repo_config:
                return {
                    "success": False,
                    "error": f"Repository '{repo_name}' not found in configuration",
                }

            if not repo_config.repo_path.exists():
                return {
                    "repository": repo_name,
                    "exists": False,
                    "can_sync": False,
                    "reason": "Repository path does not exist",
                }

            if not (repo_config.repo_path / ".git").exists():
                return {
                    "repository": repo_name,
                    "exists": True,
                    "can_sync": False,
                    "reason": "Not a git repository",
                }

            # Check git repository status
            repo = pygit2.Repository(str(repo_config.repo_path))

            # Get remote information
            remote_name = "origin"
            try:
                repo.remotes[remote_name]  # type: ignore[attr-defined]
                has_remote = True
            except KeyError:
                has_remote = False

            # Get branch information
            try:
                head_ref = repo.head.shorthand if repo.head else None
                head_commit = str(repo.head.target) if repo.head else None
            except pygit2.GitError:
                head_ref = None
                head_commit = None

            # Get last modification time
            git_dir = repo_config.repo_path / ".git"
            last_modified = git_dir.stat().st_mtime if git_dir.exists() else None

            return {
                "repository": repo_name,
                "exists": True,
                "can_sync": has_remote,
                "has_remote": has_remote,
                "remote_name": remote_name if has_remote else None,
                "head_ref": head_ref,
                "head_commit": head_commit,
                "last_modified": last_modified,
                "repo_path": str(repo_config.repo_path),
            }

        except Exception as e:
            logger.error(f"Failed to get sync status for {repo_name}: {e}")
            return {
                "repository": repo_name,
                "success": False,
                "error": str(e),
            }

    def check_for_updates(self, repo_name: str) -> dict[str, typing.Any]:
        """Check if repository has updates available without fetching.

        Args:
            repo_name: Repository name

        Returns:
            Update check result
        """
        try:
            repo_config = self.config_manager.get_repository_config_by_name(repo_name)
            if not repo_config:
                return {
                    "success": False,
                    "error": f"Repository '{repo_name}' not found in configuration",
                }

            if (
                not repo_config.repo_path.exists()
                or not (repo_config.repo_path / ".git").exists()
            ):
                return {
                    "repository": repo_name,
                    "can_check": False,
                    "reason": "Repository not available locally",
                }

            repo = pygit2.Repository(str(repo_config.repo_path))

            # This is a simplified check - in a full implementation,
            # we would compare local refs with remote refs
            remote_name = "origin"
            try:
                repo.remotes[remote_name]  # type: ignore[attr-defined]
            except KeyError:
                return {
                    "repository": repo_name,
                    "can_check": False,
                    "reason": f"Remote '{remote_name}' not found",
                }

            # Get current head
            head_commit = str(repo.head.target) if repo.head else None

            # For now, just return current state
            # A full implementation would fetch refs and compare
            return {
                "repository": repo_name,
                "can_check": True,
                "head_commit": head_commit,
                "needs_update": None,  # Would require actual remote comparison
                "message": "Update check requires fetch operation",
            }

        except Exception as e:
            logger.error(f"Failed to check for updates in {repo_name}: {e}")
            return {
                "repository": repo_name,
                "success": False,
                "error": str(e),
            }


# Global synchronizer instance
_synchronizer: RepositorySynchronizer | None = None


def get_repository_synchronizer() -> RepositorySynchronizer:
    """Get the global repository synchronizer instance."""
    global _synchronizer
    if _synchronizer is None:
        _synchronizer = RepositorySynchronizer()
    return _synchronizer
