"""Asynchronous repository management with pygit2 integration."""

import asyncio
import pathlib
import time
import typing

from loguru import logger
import pygit2


if typing.TYPE_CHECKING:
    from ca_bhfuil.core import config

from ca_bhfuil.core.git import async_git
from ca_bhfuil.core.git import repository as repository_module
from ca_bhfuil.core.models import commit as commit_models
from ca_bhfuil.core.models import results as results_models


class AsyncRepositoryManager:
    """Manages concurrent repository operations with pygit2 integration."""

    def __init__(self, max_concurrent_tasks: int = 5):
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.git_manager = async_git.AsyncGitManager()

    async def run_concurrently(
        self, tasks: list[typing.Awaitable[typing.Any]]
    ) -> list[typing.Any]:
        """Run a list of awaitables concurrently, with a semaphore."""

        async def wrapper(
            task: typing.Awaitable[typing.Any],
        ) -> typing.Any:
            async with self._semaphore:
                return await task

        return await asyncio.gather(
            *[wrapper(task) for task in tasks], return_exceptions=True
        )

    async def detect_repository(
        self, path: pathlib.Path | str
    ) -> results_models.OperationResult:
        """Detect if a path contains a valid git repository."""
        start_time = time.time()
        repo_path = pathlib.Path(path)

        try:
            # Try to find the repository root
            discovered_path = await self.git_manager.run_in_executor(
                self._discover_repository, repo_path
            )

            if discovered_path:
                # Validate the repository
                is_valid = await self.git_manager.run_in_executor(
                    self._validate_repository, discovered_path
                )

                if is_valid:
                    logger.debug(f"Valid repository detected at {discovered_path}")
                    return results_models.OperationResult(
                        success=True,
                        duration=time.time() - start_time,
                        result={"repository_path": str(discovered_path)},
                    )
                logger.warning(f"Invalid repository at {discovered_path}")
                return results_models.OperationResult(
                    success=False,
                    duration=time.time() - start_time,
                    error="Invalid repository found",
                )
            logger.debug(f"No repository found at {repo_path}")
            return results_models.OperationResult(
                success=False,
                duration=time.time() - start_time,
                error="No git repository found",
            )

        except Exception as e:
            logger.error(f"Repository detection failed for {repo_path}: {e}")
            return results_models.OperationResult(
                success=False, duration=time.time() - start_time, error=str(e)
            )

    async def get_repository_info(
        self, repo_path: pathlib.Path | str
    ) -> results_models.OperationResult:
        """Get basic information about a repository."""
        start_time = time.time()

        try:
            repo_info = await self.git_manager.run_in_executor(
                self._get_repository_info, pathlib.Path(repo_path)
            )

            return results_models.OperationResult(
                success=True, duration=time.time() - start_time, result=repo_info
            )

        except Exception as e:
            logger.error(f"Failed to get repository info for {repo_path}: {e}")
            return results_models.OperationResult(
                success=False, duration=time.time() - start_time, error=str(e)
            )

    async def get_repository(
        self, repo_path: pathlib.Path | str
    ) -> results_models.OperationResult:
        """Get a Repository wrapper for the given path.

        Args:
            repo_path: Path to the repository.

        Returns:
            OperationResult with Repository instance or error.
        """
        start_time = time.time()

        try:
            repo = await self.git_manager.run_in_executor(
                repository_module.Repository, pathlib.Path(repo_path)
            )

            return results_models.OperationResult(
                success=True, duration=time.time() - start_time, result=repo
            )

        except Exception as e:
            logger.error(f"Failed to load repository at {repo_path}: {e}")
            return results_models.OperationResult(
                success=False, duration=time.time() - start_time, error=str(e)
            )

    async def lookup_commit(
        self, repo_path: pathlib.Path | str, sha: str
    ) -> results_models.OperationResult:
        """Look up a commit by SHA (full or partial)."""
        start_time = time.time()

        try:
            # Use the Repository wrapper for consistency
            repo_result = await self.get_repository(repo_path)
            if not repo_result.success:
                return repo_result

            repo = repo_result.result
            commit_info = await self.git_manager.run_in_executor(repo.get_commit, sha)

            if commit_info:
                return results_models.OperationResult(
                    success=True, duration=time.time() - start_time, result=commit_info
                )
            return results_models.OperationResult(
                success=False,
                duration=time.time() - start_time,
                error=f"Commit not found: {sha}",
            )

        except Exception as e:
            logger.error(f"Commit lookup failed for {sha} in {repo_path}: {e}")
            return results_models.OperationResult(
                success=False, duration=time.time() - start_time, error=str(e)
            )

    async def search_commits(
        self, repo_path: pathlib.Path | str, pattern: str, max_results: int = 100
    ) -> results_models.SearchResult:
        """Search for commits by message pattern."""
        start_time = time.time()

        try:
            repo_result = await self.get_repository(repo_path)
            if not repo_result.success:
                return results_models.SearchResult(
                    success=False,
                    duration=time.time() - start_time,
                    error=repo_result.error,
                )

            repo = repo_result.result
            matches = await self.git_manager.run_in_executor(
                repo.get_commits_by_pattern, pattern, max_results
            )

            return results_models.SearchResult(
                success=True, duration=time.time() - start_time, matches=matches
            )

        except Exception as e:
            logger.error(f"Commit search failed for '{pattern}' in {repo_path}: {e}")
            return results_models.SearchResult(
                success=False, duration=time.time() - start_time, error=str(e)
            )

    async def get_branches(
        self, repo_path: pathlib.Path | str, include_remote: bool = True
    ) -> results_models.OperationResult:
        """Get all branches in the repository."""
        start_time = time.time()

        try:
            repo_result = await self.get_repository(repo_path)
            if not repo_result.success:
                return repo_result

            repo = repo_result.result
            branches = await self.git_manager.run_in_executor(
                repo.list_branches, include_remote
            )

            return results_models.OperationResult(
                success=True, duration=time.time() - start_time, result=branches
            )

        except Exception as e:
            logger.error(f"Branch listing failed for {repo_path}: {e}")
            return results_models.OperationResult(
                success=False, duration=time.time() - start_time, error=str(e)
            )

    def _discover_repository(self, path: pathlib.Path) -> pathlib.Path | None:
        """Discover git repository starting from path."""
        try:
            # Start with the given path and walk up the directory tree
            current_path = path.resolve()

            while current_path != current_path.parent:
                git_dir = current_path / ".git"
                if git_dir.exists():
                    return current_path
                current_path = current_path.parent

            return None

        except Exception:
            return None

    def _validate_repository(self, repo_path: pathlib.Path) -> bool:
        """Validate that a path contains a valid git repository."""
        try:
            pygit2.Repository(str(repo_path))
            return True
        except (pygit2.GitError, KeyError):
            return False

    def _get_repository_info(self, repo_path: pathlib.Path) -> dict[str, typing.Any]:
        """Get basic information about a repository."""
        repo = pygit2.Repository(str(repo_path))

        # Get head information
        head_name = None
        head_sha = None
        if not repo.head_is_unborn:
            head_name = repo.head.shorthand
            head_sha = str(repo.head.target)

        # Count branches and remotes
        local_branches = list(repo.branches.local)  # type: ignore[attr-defined]
        remote_branches = list(repo.branches.remote)  # type: ignore[attr-defined]
        remotes = [remote.name for remote in repo.remotes]  # type: ignore[attr-defined]

        # Get repository state
        repo_state = "clean"
        if repo.head_is_unborn:
            repo_state = "empty"

        return {
            "path": str(repo_path),
            "head_branch": head_name,
            "head_sha": head_sha,
            "local_branches": len(local_branches),
            "remote_branches": len(remote_branches),
            "remotes": remotes,
            "state": repo_state,
            "is_bare": repo.is_bare,
            "workdir": str(repo.workdir) if repo.workdir else None,
        }

    def _lookup_commit(
        self, repo_path: pathlib.Path, sha: str
    ) -> commit_models.CommitInfo | None:
        """Look up a commit by SHA (full or partial)."""
        repo = pygit2.Repository(str(repo_path))

        try:
            # Try exact match first
            commit = repo[sha] if len(sha) == 40 else repo.revparse_single(sha)  # type: ignore[index]

            if not isinstance(commit, pygit2.Commit):
                return None

            # Convert pygit2.Commit to CommitInfo
            return self._commit_to_model(commit)

        except (KeyError, pygit2.GitError):
            return None

    def _commit_to_model(self, commit: pygit2.Commit) -> commit_models.CommitInfo:
        """Convert pygit2.Commit to CommitInfo model."""
        import datetime

        return commit_models.CommitInfo(
            sha=str(commit.id),
            short_sha=str(commit.id)[:7],
            message=commit.message,
            author_name=commit.author.name,
            author_email=commit.author.email,
            author_date=datetime.datetime.fromtimestamp(
                commit.author.time,
                tz=datetime.timezone(datetime.timedelta(minutes=commit.author.offset)),
            ),
            committer_name=commit.committer.name,
            committer_email=commit.committer.email,
            committer_date=datetime.datetime.fromtimestamp(
                commit.committer.time,
                tz=datetime.timezone(
                    datetime.timedelta(minutes=commit.committer.offset)
                ),
            ),
            parents=[str(parent.id) for parent in commit.parents],
            files_changed=None,  # Could be calculated if needed
            insertions=None,  # Could be calculated if needed
            deletions=None,  # Could be calculated if needed
        )

    async def register_repository_with_tracking(
        self, repo_config: "config.RepositoryConfig"
    ) -> results_models.OperationResult:
        """Register repository in registry and update state.

        Args:
            repo_config: Repository configuration

        Returns:
            Operation result with registry information
        """
        start_time = time.time()

        try:
            from ca_bhfuil.core import async_registry

            registry = await async_registry.get_async_repository_registry()

            # Register the repository
            repo_id = await registry.register_repository(repo_config)

            # Get repository statistics if it exists
            if repo_config.repo_path.exists():
                repo_result = await self.get_repository(repo_config.repo_path)
                if repo_result.success:
                    repo = repo_result.result
                    branches = await self.git_manager.run_in_executor(
                        repo.list_branches
                    )
                    # For commit count, we'd need to walk the repository
                    # For now, use 0 as placeholder
                    commit_count = 0
                    branch_count = len(branches)

                    # Update statistics
                    await registry.update_repository_stats(
                        repo_config.name, commit_count, branch_count
                    )

            return results_models.OperationResult(
                success=True,
                duration=time.time() - start_time,
                result={"repository_id": repo_id, "name": repo_config.name},
            )

        except Exception as e:
            logger.error(f"Failed to register repository {repo_config.name}: {e}")
            return results_models.OperationResult(
                success=False, duration=time.time() - start_time, error=str(e)
            )

    async def analyze_and_store_repository(
        self, repo_name: str
    ) -> results_models.OperationResult:
        """Analyze repository and store commits in registry.

        Args:
            repo_name: Repository name from configuration

        Returns:
            Operation result with analysis statistics
        """
        start_time = time.time()

        try:
            from ca_bhfuil.core import async_config
            from ca_bhfuil.core import async_registry

            # Get repository configuration
            config_manager = async_config.AsyncConfigManager()
            repo_config = await config_manager.get_repository_config_by_name(repo_name)
            if not repo_config:
                return results_models.OperationResult(
                    success=False,
                    duration=time.time() - start_time,
                    error=f"Repository '{repo_name}' not found in configuration",
                )

            # Get repository
            repo_result = await self.get_repository(repo_config.repo_path)
            if not repo_result.success:
                return repo_result

            repo = repo_result.result
            registry = await async_registry.get_async_repository_registry()

            # Get branches and analyze
            branches = await self.git_manager.run_in_executor(repo.list_branches)
            commits_analyzed = 0

            # For now, just get basic stats
            # In a full implementation, we'd walk commits and store them
            logger.info(f"Repository {repo_name} has {len(branches)} branches")

            # Update repository statistics
            await registry.update_repository_stats(
                repo_name, commits_analyzed, len(branches)
            )

            return results_models.OperationResult(
                success=True,
                duration=time.time() - start_time,
                result={
                    "repository": repo_name,
                    "branches": len(branches),
                    "commits_analyzed": commits_analyzed,
                },
            )

        except Exception as e:
            logger.error(f"Failed to analyze repository {repo_name}: {e}")
            return results_models.OperationResult(
                success=False, duration=time.time() - start_time, error=str(e)
            )

    async def get_repository_state(
        self, repo_name: str
    ) -> results_models.OperationResult:
        """Get comprehensive repository state from registry.

        Args:
            repo_name: Repository name

        Returns:
            Operation result with repository state
        """
        start_time = time.time()

        try:
            from ca_bhfuil.core import async_registry

            registry = await async_registry.get_async_repository_registry()
            state = await registry.get_repository_state(repo_name)

            if state:
                return results_models.OperationResult(
                    success=True, duration=time.time() - start_time, result=state
                )
            return results_models.OperationResult(
                success=False,
                duration=time.time() - start_time,
                error=f"Repository '{repo_name}' not found",
            )

        except Exception as e:
            logger.error(f"Failed to get repository state for {repo_name}: {e}")
            return results_models.OperationResult(
                success=False, duration=time.time() - start_time, error=str(e)
            )

    def shutdown(self) -> None:
        """Shutdown the git manager and clean up resources."""
        self.git_manager.shutdown()
