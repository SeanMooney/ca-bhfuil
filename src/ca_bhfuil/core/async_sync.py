"""Async repository synchronization for keeping repositories up to date."""

import asyncio
import time
import typing

from loguru import logger
import pygit2

from ca_bhfuil.core import async_config
from ca_bhfuil.core import async_registry
from ca_bhfuil.core import config
from ca_bhfuil.core.git import async_git
from ca_bhfuil.core.git import repository as repository_module
from ca_bhfuil.core.managers import factory as manager_factory
from ca_bhfuil.core.models import results as results_models


class AsyncRepositorySynchronizer:
    """Handles asynchronous synchronization of git repositories."""

    def __init__(
        self,
        config_manager: async_config.AsyncConfigManager | None = None,
        repo_registry: async_registry.AsyncRepositoryRegistry | None = None,
        git_manager: async_git.AsyncGitManager | None = None,
    ) -> None:
        """Initialize async repository synchronizer.

        Args:
            config_manager: Async configuration manager instance
            repo_registry: Async repository registry instance
            git_manager: Async git manager instance
        """
        self.config_manager = config_manager or async_config.AsyncConfigManager()
        self.repo_registry = repo_registry or async_registry.AsyncRepositoryRegistry()
        self.git_manager = git_manager or async_git.AsyncGitManager()
        self._sync_semaphore = asyncio.Semaphore(3)  # Limit concurrent syncs
        logger.debug("Initialized async repository synchronizer")

    async def sync_repository(self, repo_name: str) -> results_models.OperationResult:
        """Synchronize a single repository asynchronously.

        Args:
            repo_name: Repository name

        Returns:
            Operation result with sync information
        """
        async with self._sync_semaphore:
            start_time = time.time()

            try:
                # Get repository configuration
                repo_config = await self.config_manager.get_repository_config_by_name(
                    repo_name
                )
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

                # Check if it's a git repository (handle both regular and bare repos)
                if not (
                    (repo_config.repo_path / ".git").exists()
                    or (repo_config.repo_path / "refs").exists()
                ):
                    return results_models.OperationResult(
                        success=False,
                        duration=time.time() - start_time,
                        error=f"Not a git repository: {repo_config.repo_path}",
                    )

                # Perform synchronization using sync manager in executor
                sync_result = await self.git_manager.run_in_executor(
                    self._perform_sync_sync, repo_config
                )

                # Update registry with latest state and sync commits to database
                if sync_result["success"]:
                    await self._update_registry_after_sync(repo_config, sync_result)

                    # Get repository manager and sync to database
                    try:
                        repo_manager = await manager_factory.get_repository_manager(
                            repo_config.repo_path
                        )
                        await repo_manager.sync_with_database()
                        logger.info(f"Synced {repo_config.name} commits to database")
                    except Exception as e:
                        logger.warning(
                            f"Failed to sync {repo_config.name} commits to database: {e}"
                        )
                        # Don't fail the overall sync operation if database sync fails

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

    def _perform_sync_sync(
        self, repo_config: config.RepositoryConfig
    ) -> dict[str, typing.Any]:
        """Perform synchronization (for executor).

        Args:
            repo_config: Repository configuration

        Returns:
            Sync result dictionary
        """
        # Basic sync implementation - just check if repo exists and is valid
        repo_path = repo_config.repo_path
        if not repo_path.exists():
            return {
                "success": False,
                "error": f"Repository path does not exist: {repo_path}",
                "commits_before": 0,
                "commits_after": 0,
            }

        # Check if it's a git repository (handle both regular and bare repos)
        if not ((repo_path / ".git").exists() or (repo_path / "refs").exists()):
            return {
                "success": False,
                "error": f"Not a git repository: {repo_path}",
                "commits_before": 0,
                "commits_after": 0,
            }

        try:
            # Open repository and get basic stats
            repo = pygit2.Repository(str(repo_path))
            commit_count = len(list(repo.walk(repo.head.target)))
            return {
                "success": True,
                "commits_before": commit_count,
                "commits_after": commit_count,
                "repository": repo_config.name,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "commits_before": 0,
                "commits_after": 0,
            }

    async def _update_registry_after_sync(
        self,
        repo_config: config.RepositoryConfig,
        sync_result: dict[str, typing.Any],
    ) -> None:
        """Update repository registry after successful sync.

        Args:
            repo_config: Repository configuration
            sync_result: Sync operation result
        """
        try:
            # Get updated repository statistics
            repo_wrapper = await self.git_manager.run_in_executor(
                repository_module.Repository, repo_config.repo_path
            )
            branches = await self.git_manager.run_in_executor(
                repo_wrapper.list_branches
            )
            branch_count = len(branches)

            # For commit count, use the sync result
            commit_count = sync_result.get("commits_after", 0)

            # Update registry stats
            await self.repo_registry.update_repository_stats(
                repo_config.name, commit_count, branch_count
            )

            logger.debug(
                f"Updated registry stats for {repo_config.name}: "
                f"{commit_count} commits, {branch_count} branches"
            )

        except Exception as e:
            logger.warning(f"Failed to update registry after sync: {e}")

    async def sync_repositories_concurrently(
        self, repo_names: list[str]
    ) -> list[results_models.OperationResult]:
        """Synchronize multiple repositories concurrently.

        Args:
            repo_names: List of repository names

        Returns:
            List of operation results for each repository
        """
        logger.info(
            f"Starting concurrent synchronization of {len(repo_names)} repositories"
        )
        start_time = time.time()

        # Create sync tasks
        tasks = [self.sync_repository(repo_name) for repo_name in repo_names]

        # Run concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results: list[results_models.OperationResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Convert exception to failed OperationResult
                error_result = results_models.OperationResult(
                    success=False,
                    duration=0.0,
                    error=f"Exception during sync: {result}",
                )
                processed_results.append(error_result)
                logger.error(f"❌ {repo_names[i]} sync failed with exception: {result}")
            else:
                # result is definitely OperationResult here
                op_result = typing.cast("results_models.OperationResult", result)
                processed_results.append(op_result)
                if op_result.success:
                    logger.info(f"✅ {repo_names[i]} synchronized successfully")
                else:
                    logger.warning(f"❌ {repo_names[i]} sync failed: {op_result.error}")

        total_duration = time.time() - start_time
        successful_syncs = sum(1 for r in processed_results if r.success)
        failed_syncs = len(processed_results) - successful_syncs

        logger.info(
            f"Concurrent synchronization complete: {successful_syncs} successful, "
            f"{failed_syncs} failed, {total_duration:.2f}s total"
        )

        return processed_results

    async def sync_all_repositories(self) -> list[results_models.OperationResult]:
        """Synchronize all configured repositories concurrently.

        Returns:
            List of operation results for each repository
        """
        logger.info("Starting synchronization of all repositories")

        global_config = await self.config_manager.load_configuration()
        repo_names = [repo.name for repo in global_config.repos]

        if not repo_names:
            logger.info("No repositories configured for synchronization")
            return []

        return await self.sync_repositories_concurrently(repo_names)

    async def get_sync_status(self, repo_name: str) -> dict[str, typing.Any]:
        """Get synchronization status for a repository.

        Args:
            repo_name: Repository name

        Returns:
            Sync status information
        """
        try:
            # Get repository state from registry
            repo_state = await self.repo_registry.get_repository_state(repo_name)
            if not repo_state:
                return {
                    "repository": repo_name,
                    "success": False,
                    "error": "Repository not found",
                }

            return {
                "repository": repo_name,
                "success": True,
                "exists": repo_state.get("exists", False),
                "is_git_repo": repo_state.get("is_git_repo", False),
                "registered": repo_state.get("registered", False),
                "last_analyzed": repo_state.get("last_analyzed"),
                "commit_count": repo_state.get("commit_count", 0),
                "branch_count": repo_state.get("branch_count", 0),
            }

        except Exception as e:
            logger.error(f"Failed to get sync status for {repo_name}: {e}")
            return {
                "repository": repo_name,
                "success": False,
                "error": str(e),
            }

    async def check_for_updates(self, repo_name: str) -> dict[str, typing.Any]:
        """Check if repository has updates available without fetching.

        Args:
            repo_name: Repository name

        Returns:
            Update check result
        """
        try:
            # Get repository config
            repo_config = await self.config_manager.get_repository_config_by_name(
                repo_name
            )
            if not repo_config:
                return {
                    "repository": repo_name,
                    "success": False,
                    "error": "Repository configuration not found",
                }

            # Check if repository exists and is valid
            if not repo_config.repo_path.exists():
                return {
                    "repository": repo_name,
                    "success": False,
                    "error": "Repository path does not exist",
                }

            # Basic implementation - assume no updates available for now
            # In a full implementation, this would check remote refs
            return {
                "repository": repo_name,
                "success": True,
                "updates_available": False,
                "behind_by": 0,
                "ahead_by": 0,
            }

        except Exception as e:
            logger.error(f"Failed to check for updates in {repo_name}: {e}")
            return {
                "repository": repo_name,
                "success": False,
                "error": str(e),
            }

    async def get_all_sync_status(self) -> list[dict[str, typing.Any]]:
        """Get sync status for all configured repositories.

        Returns:
            List of sync status for each repository
        """
        logger.info("Getting sync status for all repositories")

        global_config = await self.config_manager.load_configuration()
        repo_names = [repo.name for repo in global_config.repos]

        if not repo_names:
            logger.info("No repositories configured")
            return []

        # Get status concurrently
        tasks = [self.get_sync_status(repo_name) for repo_name in repo_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        status_list: list[dict[str, typing.Any]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                status_list.append(
                    {
                        "repository": repo_names[i],
                        "success": False,
                        "error": str(result),
                    }
                )
            else:
                # result is definitely dict here
                status_dict = typing.cast("dict[str, typing.Any]", result)
                status_list.append(status_dict)

        return status_list

    async def get_sync_summary(self) -> dict[str, typing.Any]:
        """Get a summary of synchronization status across all repositories.

        Returns:
            Sync summary statistics
        """
        status_list = await self.get_all_sync_status()

        total_repos = len(status_list)
        can_sync = sum(1 for s in status_list if s.get("can_sync", False))
        cannot_sync = total_repos - can_sync
        has_errors = sum(1 for s in status_list if not s.get("success", True))

        # Get registry stats
        registry_stats = await self.repo_registry.get_registry_stats()

        return {
            "total_repositories": total_repos,
            "can_sync": can_sync,
            "cannot_sync": cannot_sync,
            "has_errors": has_errors,
            "registry_stats": registry_stats,
            "last_check": time.time(),
        }

    def shutdown(self) -> None:
        """Shutdown the synchronizer and clean up resources."""
        self.git_manager.shutdown()


# Global async synchronizer instance
_async_synchronizer: AsyncRepositorySynchronizer | None = None


async def get_async_repository_synchronizer() -> AsyncRepositorySynchronizer:
    """Get the global async repository synchronizer instance."""
    global _async_synchronizer
    if _async_synchronizer is None:
        _async_synchronizer = AsyncRepositorySynchronizer()
    return _async_synchronizer
